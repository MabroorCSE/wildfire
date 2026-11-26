#pragma once

#include <ostream>
#include <string>

struct CellCommand
{
    std::string targetCellId;
    double litresDropped = 0.0;
};

inline std::ostream& operator<<(std::ostream& os, const CellCommand& c)
{
    return os << c.targetCellId << "," << c.litresDropped;
}
