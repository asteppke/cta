#ifndef TRACING_H
#define TRACING_H

#include "epicsThread.h"

#include <stdio.h>
#include <time.h>
#include <sys/time.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <stdbool.h>

/*
 * This header file provides a simple tracing infrastructure.
 *
 * How to use tracing:
 * (1) Define a trace point.
 * (2) Put a trace macro into your code and provide the trace point and
 *     the trace message as argument. The trace message may be in printf
 *     style.
 * (3) During run time the trace level of the trace macro and the trace level
 *     of the trace point is compared. If the trace level of the trace macro 
 *     is smaller or equal than the trace level of the trace point, the message is
 *     emitted.
 *
 * Example:
 * TracePoint tp = {TRACE_LEVEL_INFO, "myTracePoint"};
 * TRACE_NOTICE(tp, ("tp.level=%u, tp.name=%s", tp.level, tp.name)); // emitted
 * TRACE_INFO(  tp, ("this is a info message")); // emitted
 * TRACE_DEBUG( tp, ("this is a debug message")); // not emitted
 *
 * A trace output has the following format:
 * <date> <time> <trace point name> <thread name> <trace message level> <trace message>
 * The next line is an example:
 * 2016-03-05 14:02:25_230898 etaTestIntDelivery   [CAS-client] INFO     : event handler called (numOfEvents=1)
 */

#define TRACE_IS_ENABLED 1

#define TRACE_LEVEL_NONE 0
#define TRACE_LEVEL_EMERGENCY 1
#define TRACE_LEVEL_ALERT 2
#define TRACE_LEVEL_CRITICAL 3
#define TRACE_LEVEL_ERROR 4
#define TRACE_LEVEL_WARNING 5
#define TRACE_LEVEL_NOTICE 6
#define TRACE_LEVEL_INFO 7
#define TRACE_LEVEL_DEBUG 8

/* trace point */
typedef struct {
  int *level;
  const char* name;
} TracePoint;

/* trace macros */
#if TRACE_IS_ENABLED
#define TRACE_EMERGENCY(TP, MSG) TRACE(TRACE_LEVEL_EMERGENCY,  "EMERGENCY", TP, MSG)
#define TRACE_ALERT(    TP, MSG) TRACE(TRACE_LEVEL_ALERT    ,  "ALERT"    , TP, MSG)
#define TRACE_CRITICAL( TP, MSG) TRACE(TRACE_LEVEL_CRITICAL ,  "CRITICAL" , TP, MSG)
#define TRACE_ERROR(    TP, MSG) TRACE(TRACE_LEVEL_ERROR    ,  "ERROR"    , TP, MSG)
#define TRACE_WARNING(  TP, MSG) TRACE(TRACE_LEVEL_WARNING  ,  "WARNING"  , TP, MSG)
#define TRACE_NOTICE(   TP, MSG) TRACE(TRACE_LEVEL_NOTICE   ,  "NOTICE"   , TP, MSG)
#define TRACE_INFO(     TP, MSG) TRACE(TRACE_LEVEL_INFO     ,  "INFO"     , TP, MSG)
#define TRACE_DEBUG(    TP, MSG) TRACE((TRACE_LEVEL_DEBUG)  ,  "DEBUG"    , TP, MSG)

#define TRACE(LEVEL, LEVEL_NAME, TP, MSG) \
  do { if ((LEVEL)<=*(TP).level) { \
         struct timeval tv; \
         struct tm bdt; \
         gettimeofday(&tv, NULL); \
         gmtime_r(&tv.tv_sec, &bdt); \
         printf("%04d-%02d-%02d %02d:%02d:%02d_%06ld ", bdt.tm_year + 1900, bdt.tm_mon, bdt.tm_mday, bdt.tm_hour, bdt.tm_min, bdt.tm_sec, tv.tv_usec); \
         printf("%-20.20s ", (TP).name); \
         printf("[%s] ", epicsThreadGetNameSelf()); \
         printf("%-9s: ", (LEVEL_NAME)); \
         printf MSG; \
         printf("\n"); \
       } \
  } while(false)
#define TRACE_IS_LEVEL_MET(TP, TL) (*(TP).level >= (TL))
#else
#define TRACE_EMERGENCY(TP, MSG) 
#define TRACE_ALERT(TP, MSG) 
#define TRACE_CRITICAL(TP, MSG) 
#define TRACE_ERROR(TP, MSG) 
#define TRACE_WARNING(TP, MSG)
#define TRACE_NOTICE(TP, MSG)
#define TRACE_INFO(TP, MSG)
#define TRACE_DEBUG(TP, MSG)
#define TRACE_IS_LEVEL_MET(TP, TL) (0)
#endif

#endif

