#pragma once

#include <iostream>
#include <limits>
#include <string>
#include <cadmium/core/modeling/atomic.hpp>
#include <cadmium/celldevs/core/msg.hpp>
#include "cell_command.hpp"
#include "state.hpp"
#include <cmath>

enum class AircraftPhase
{
    Idle,
    FlyingToTarget,
    Dropping,
    Returning,
    Refilling
};

struct AircraftState
{
    double x;
    double y;
    double targetX;
    double targetY;
    double waterLeft;
    AircraftPhase phase;
    double sigma;
    std::string targetCellId;

    explicit AircraftState(double baseX, double baseY, double tankSize)
        : x(baseX), y(baseY), targetX(baseX), targetY(baseY), waterLeft(tankSize), phase(AircraftPhase::Idle), sigma(std::numeric_limits<double>::infinity()), targetCellId(""){}
};

inline std::ostream& operator<<(std::ostream& os, const AircraftState& s)
{
    return os << s.x << "," << s.y << "," << s.targetX << "," << s.targetY << "," << s.waterLeft << "," << static_cast<int>(s.phase) << "," << s.sigma;
}

//ids come from config, '_' is assumed present
inline std::pair<double, double> parseCellId(const std::string& id)
{
    size_t i = id.find('_');
    double x = std::stod(id.substr(0, i));
    double y = std::stod(id.substr(i+1));
    return {x, y};
}

class Aircraft : public cadmium::Atomic<AircraftState>
{
    public:
        cadmium::Port<CellCommand> cellCommandOut;
        cadmium::Port<CellCommand> orderIn;
        cadmium::Port<std::string> readyOut;

        double baseX;
        double baseY;
        double tankSize;
        double flowRate;
        double refillTime;
        double speed;

        explicit Aircraft(const std::string& id, double baseX, double baseY, double tankSize, double flowRate, double refillTime, double speed = 50.0)
            : cadmium::Atomic<AircraftState>(id, AircraftState(baseX, baseY, tankSize)),
            baseX(baseX), baseY(baseY), tankSize(tankSize), flowRate(flowRate), refillTime(refillTime), speed(speed)
        {
            orderIn = addInPort<CellCommand>("orderIn");
            readyOut = addOutPort<std::string>("readyOut");
            cellCommandOut = addOutPort<CellCommand>("cellCommandOut");
        }

        void internalTransition(AircraftState& s) const override
        {

        }

        void externalTransition(AircraftState& s, double e) const override
        {

        }

        void output(const AircraftState& s) const override
        {

        }

        [[nodiscard]] double timeAdvance(const AircraftState& s) const override
        {
            return s.sigma;
        }
};

