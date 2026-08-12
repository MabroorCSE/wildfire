#pragma once

#include <ostream>
#include <string>

struct CellCommand
{
    std::string targetCellId;
};

inline std::ostream& operator<<(std::ostream& os, const CellCommand& c)
{
    return os << c.targetCellId;
}
