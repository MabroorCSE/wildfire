
#include <cadmium/core/logger/csv.hpp>
#include <cadmium/core/simulation/root_coordinator.hpp>
#include <fstream>
#include <iostream>
#include <string>
#include "include/state.hpp"
#include "include/hybrid_coupled.hpp"
#include "include/logger.hpp"



std::chrono::system_clock::time_point parseDateTime(const std::string& start_time_str) {
    std::tm tm = {};
    std::istringstream ss(start_time_str);
    ss >> std::get_time(&tm, "%Y-%m-%d %H:%M:%S");  
    if (ss.fail()) {
        throw std::runtime_error("Failed to parse date/time string");
    }
    // Convert std::tm to time_t (epoch time)
    tm.tm_isdst = -1; 
    time_t datime = std::mktime(&tm);
    
    
    // Convert to time_point
    return std::chrono::system_clock::from_time_t(datime);
    }


int main(int argc, char** argv)
{
    if (argc < 3)
    {
        std::cout << "Missing source json and destination csv" << std::endl;
        return 1;
    }
    

    std::string start_time_str = argv[3];
    auto start_time = parseDateTime(start_time_str);

    auto model = std::make_shared<WildfireHybridCoupled>("hybrid", argv[1]);

    auto rootCoordinator = cadmium::RootCoordinator(model);
	auto logger = std::make_shared<Logger>(argv[2], start_time);

    rootCoordinator.setLogger(logger);
    rootCoordinator.start();
	rootCoordinator.simulate(200000.0);
	rootCoordinator.stop();
    return 0;
}