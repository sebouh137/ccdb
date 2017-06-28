//
// Created by romanov on 6/27/17.
//

#ifndef CCDB_PERFLOG_H
#define CCDB_PERFLOG_H

#include <iostream>
#include <string>

#include "StopWatch.h"

#if CCDB_PERFLOG_ON
#define CCDB_PERFLOG(x) (PerfLog(x))
#else
#define CCDB_PERF_LOG(x)
#endif

namespace ccdb{
    class PerfLog{
    public:
        explicit PerfLog (const std::string& name):
                _sw(),
                _name(name)
        {
        }

        PerfLog(PerfLog&) = default;
        PerfLog(PerfLog&&) noexcept;


        ~PerfLog(){
            std::cout<<"CCDB_PERF_LOG: "<<_name<<" us: "<<_sw.ElapsedUs()<<std::endl;
        }
    private:
        ccdb::StopWatch _sw{};
        std::string _name;

    };

    inline PerfLog::PerfLog(PerfLog&&) noexcept = default;
}
#endif //CCDB_PERFLOG_H