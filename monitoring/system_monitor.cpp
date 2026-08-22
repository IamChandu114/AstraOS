#include <algorithm>
#include <chrono>
#include <csignal>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

namespace fs = std::filesystem;

static volatile std::sig_atomic_t running = 1;

struct CpuTimes {
    unsigned long long user = 0;
    unsigned long long nice = 0;
    unsigned long long system = 0;
    unsigned long long idle = 0;
    unsigned long long iowait = 0;
    unsigned long long irq = 0;
    unsigned long long softirq = 0;
    unsigned long long steal = 0;

    unsigned long long idle_all() const { return idle + iowait; }
    unsigned long long total() const {
        return user + nice + system + idle + iowait + irq + softirq + steal;
    }
};

struct ProcessInfo {
    int pid = 0;
    std::string name;
    char state = '?';
    unsigned long long cpu_ticks = 0;
    long rss_pages = 0;
    int threads = 0;
};

static void on_signal(int) { running = 0; }

static std::optional<CpuTimes> read_cpu_times() {
    std::ifstream stat("/proc/stat");
    std::string cpu;
    CpuTimes t;
    if (stat >> cpu >> t.user >> t.nice >> t.system >> t.idle >> t.iowait >> t.irq >> t.softirq >> t.steal) {
        return t;
    }
    return std::nullopt;
}

static double cpu_usage(const CpuTimes& prev, const CpuTimes& cur) {
    const auto idle_delta = cur.idle_all() - prev.idle_all();
    const auto total_delta = cur.total() - prev.total();
    if (total_delta == 0) return 0.0;
    return 100.0 * static_cast<double>(total_delta - idle_delta) / static_cast<double>(total_delta);
}

static std::pair<unsigned long long, unsigned long long> read_mem_kb() {
    std::ifstream meminfo("/proc/meminfo");
    std::string key, unit;
    unsigned long long value = 0;
    unsigned long long total = 0, available = 0;
    while (meminfo >> key >> value >> unit) {
        if (key == "MemTotal:") total = value;
        if (key == "MemAvailable:") available = value;
    }
    return {total, available};
}

static std::optional<double> read_temperature_c() {
    double hottest = -1.0;
    for (const auto& entry : fs::directory_iterator("/sys/class/thermal")) {
        auto temp_path = entry.path() / "temp";
        std::ifstream temp(temp_path);
        double raw = 0;
        if (temp >> raw) {
            double c = raw > 1000 ? raw / 1000.0 : raw;
            hottest = std::max(hottest, c);
        }
    }
    if (hottest >= 0) return hottest;
    return std::nullopt;
}

static std::string read_battery_state() {
    for (const auto& entry : fs::directory_iterator("/sys/class/power_supply")) {
        std::ifstream type_file(entry.path() / "type");
        std::string type;
        if (!(type_file >> type) || type != "Battery") continue;

        std::ifstream status_file(entry.path() / "status");
        std::ifstream capacity_file(entry.path() / "capacity");
        std::string status = "Unknown";
        int capacity = -1;
        status_file >> status;
        capacity_file >> capacity;
        std::ostringstream out;
        out << status;
        if (capacity >= 0) out << " " << capacity << "%";
        return out.str();
    }
    return "AC/Unknown";
}

static unsigned long long read_network_bytes() {
    std::ifstream net("/proc/net/dev");
    std::string line;
    unsigned long long total = 0;
    std::getline(net, line);
    std::getline(net, line);
    while (std::getline(net, line)) {
        std::replace(line.begin(), line.end(), ':', ' ');
        std::istringstream iss(line);
        std::string iface;
        unsigned long long rx = 0, tx = 0, skip = 0;
        iss >> iface >> rx;
        for (int i = 0; i < 7; ++i) iss >> skip;
        iss >> tx;
        if (iface != "lo") total += rx + tx;
    }
    return total;
}

static std::vector<ProcessInfo> read_processes() {
    std::vector<ProcessInfo> processes;
    for (const auto& entry : fs::directory_iterator("/proc")) {
        if (!entry.is_directory()) continue;
        const auto name = entry.path().filename().string();
        if (!std::all_of(name.begin(), name.end(), ::isdigit)) continue;

        std::ifstream stat(entry.path() / "stat");
        std::string content;
        std::getline(stat, content);
        auto l = content.find('(');
        auto r = content.rfind(')');
        if (l == std::string::npos || r == std::string::npos || r <= l) continue;

        ProcessInfo p;
        p.pid = std::stoi(name);
        p.name = content.substr(l + 1, r - l - 1);

        std::istringstream rest(content.substr(r + 2));
        std::vector<std::string> fields;
        std::string token;
        while (rest >> token) fields.push_back(token);
        if (fields.size() > 21) {
            p.state = fields[0].empty() ? '?' : fields[0][0];
            p.cpu_ticks = std::stoull(fields[11]) + std::stoull(fields[12]);
            p.threads = std::stoi(fields[17]);
            p.rss_pages = std::stol(fields[21]);
            processes.push_back(p);
        }
    }
    return processes;
}

static std::string escape_json(const std::string& value) {
    std::ostringstream out;
    for (char c : value) {
        if (c == '"' || c == '\\') out << '\\';
        out << c;
    }
    return out.str();
}

int main(int argc, char** argv) {
    int interval = 1;
    bool json = false;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--json") json = true;
        if (arg == "--interval" && i + 1 < argc) interval = std::max(1, std::stoi(argv[++i]));
    }

    std::signal(SIGINT, on_signal);
    std::signal(SIGTERM, on_signal);

    auto prev_cpu = read_cpu_times();
    auto prev_net = read_network_bytes();
    auto prev_proc = read_processes();
    std::map<int, unsigned long long> prev_ticks;
    for (const auto& p : prev_proc) prev_ticks[p.pid] = p.cpu_ticks;

    std::this_thread::sleep_for(std::chrono::seconds(interval));

    while (running) {
        auto cur_cpu = read_cpu_times();
        auto [mem_total, mem_avail] = read_mem_kb();
        auto temp = read_temperature_c();
        auto battery = read_battery_state();
        auto cur_net = read_network_bytes();
        auto processes = read_processes();

        ProcessInfo top;
        unsigned long long top_delta = 0;
        for (const auto& p : processes) {
            auto old = prev_ticks[p.pid];
            auto delta = p.cpu_ticks > old ? p.cpu_ticks - old : 0;
            if (delta > top_delta) {
                top_delta = delta;
                top = p;
            }
        }

        double cpu = (prev_cpu && cur_cpu) ? cpu_usage(*prev_cpu, *cur_cpu) : 0.0;
        double mem_used_gb = (mem_total - mem_avail) / 1024.0 / 1024.0;
        double mem_total_gb = mem_total / 1024.0 / 1024.0;
        double net_kbps = (cur_net >= prev_net) ? (cur_net - prev_net) / 1024.0 / interval : 0.0;

        if (json) {
            std::cout << "{"
                      << "\"cpu_usage\":" << std::fixed << std::setprecision(2) << cpu << ","
                      << "\"ram_used_gb\":" << mem_used_gb << ","
                      << "\"ram_total_gb\":" << mem_total_gb << ","
                      << "\"temperature_c\":" << (temp ? *temp : -1.0) << ","
                      << "\"battery\":\"" << escape_json(battery) << "\","
                      << "\"network_kbps\":" << net_kbps << ","
                      << "\"processes\":" << processes.size() << ","
                      << "\"top_process\":{\"pid\":" << top.pid << ",\"name\":\"" << escape_json(top.name)
                      << "\",\"state\":\"" << top.state << "\",\"threads\":" << top.threads << "}"
                      << "}" << std::endl;
        } else {
            std::cout << "CPU Usage: " << std::fixed << std::setprecision(1) << cpu << "%\n"
                      << "RAM Usage: " << mem_used_gb << "GB / " << mem_total_gb << "GB\n"
                      << "Temperature: " << (temp ? std::to_string(*temp) + "C" : "Unavailable") << "\n"
                      << "Battery: " << battery << "\n"
                      << "Network: " << net_kbps << " KB/s\n"
                      << "Top Process: " << top.name << " PID " << top.pid << "\n"
                      << "Active Processes: " << processes.size() << "\n---\n";
        }

        prev_cpu = cur_cpu;
        prev_net = cur_net;
        prev_ticks.clear();
        for (const auto& p : processes) prev_ticks[p.pid] = p.cpu_ticks;
        std::this_thread::sleep_for(std::chrono::seconds(interval));
    }
    return 0;
}
