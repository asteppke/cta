
#include "tracing.h"
#include "seqCtrl.h"

#include <devSup.h>
#include <aoRecord.h>
#include <aiRecord.h>
#include <longoutRecord.h>
#include <longinRecord.h>
#include <boRecord.h>
#include <epicsExport.h>
#include <errlog.h>
#include <dbScan.h>
#include <dbCommon.h>
#include <devLib.h>
#include <iocsh.h>
#include <epicsExport.h>
#include <initHooks.h>
#include <alarm.h>
#include <recGbl.h>

#include <string.h>
#include <inttypes.h>

/* tracing */
static int devSeqCtrlTraceLevel = TRACE_LEVEL_NONE;
static TracePoint tp = {&devSeqCtrlTraceLevel, "devSeqCtrl"};

/*********** analog output ************/

/* forward declarations */
long DevSeqCtrlInitAo(aoRecord *record);
long DevSeqCtrlWriteAo(aoRecord *record);

/* dset */
struct {
  long number;
  DEVSUPFUN report;
  DEVSUPFUN init;
  DEVSUPFUN init_record;
  DEVSUPFUN get_ioint_info;
  DEVSUPFUN write;
  DEVSUPFUN special_linconv;
} DevSeqCtrlAo = {
  6,
  NULL,
  NULL,
  DevSeqCtrlInitAo,
  NULL,
  DevSeqCtrlWriteAo,
  NULL
};
epicsExportAddress(dset, DevSeqCtrlAo);

/* init */
long DevSeqCtrlInitAo(aoRecord *record) {

  TRACE_INFO(tp, ("%s: running for record %s", __func__, record->name));

  return 0;
}

/* write */
long DevSeqCtrlWriteAo(aoRecord *record) {
  int status = 0;
  PulseIdEvt *evt = NULL;

  TRACE_DEBUG(tp, ("%s: record <<%s>> writes to C%d S%d",
        __func__, record->name, record->out.value.vmeio.card,
        record->out.value.vmeio.signal));

  /* SOS event is dispatched  before puse id of the sequence */
  /* is received. So the pulse id of the event is from the last */
  /* pulse. The sequence is programmed to the HW in this pulse */
  /* but the HW plays it out in the next sequence. Hence, the */
  /* sequence will be started two pulses after the pulse id */
  /* We distribute the pulse id for which the programming is */
  /* currently done. */
  evt = Q_NEW(PulseIdEvt, SOS_SIG);
  evt->pulse_id = (uint64_t) record->val + 2;
  QACTIVE_POST(AO_SeqCtrl, &evt->super, NULL);

  TRACE_DEBUG(tp, ("%s posted SOS_SIG (pulseId=%" PRIu64 ")", __func__, evt->pulse_id));

  return status;
}

/************** longout ***************/

/* forward declarations */
long devSeqCtrlInitLongout(longoutRecord *record);
long devSeqCtrlWriteLongout(longoutRecord *record);

/* dset */
struct {
  long number;
  DEVSUPFUN report;
  DEVSUPFUN init;
  DEVSUPFUN init_record;
  DEVSUPFUN get_ioint_info;
  DEVSUPFUN write_longout;
} DevSeqCtrlLongout = {
  5,
  NULL,
  NULL,
  devSeqCtrlInitLongout,
  NULL,
  devSeqCtrlWriteLongout
};
epicsExportAddress(dset, DevSeqCtrlLongout);

/* init */
long devSeqCtrlInitLongout(longoutRecord *record) {

  TRACE_INFO(tp, ("%s: running for record %s", __func__, record->name));

  /* check arguments */
  if (record->out.type != VME_IO) {
    errlogSevPrintf(errlogFatal, "%s: record<<%s>>: illegal OUT link "
        "type\n", __func__, record->name);
    return -1;
  }

  return 0;
}

/* write */
long devSeqCtrlWriteLongout(longoutRecord *record) {
  int status = 0;

  TRACE_DEBUG(tp, ("%s: record <<%s>> writes to C%d S%d",
        __func__, record->name, record->out.value.vmeio.card,
        record->out.value.vmeio.signal));

  switch (record->out.value.vmeio.signal) {
    case 0:
      SetLength((uint32_t)record->val);
      break;
    case 1:
      SetCycles((uint32_t)record->val);
      break;
    case 2:
      {
        enum StartMode mode = START_IMMEDIATELY;

        switch((uint32_t)record->val) {
          case 0: mode = START_IMMEDIATELY; break;
          case 1: mode = START_MODULO; break;
          default:
            errlogSevPrintf(errlogFatal, "%s: record<<%s>>: ilegal start mode\n"
              , __func__, record->name);
            status = -1;
        }

        SetSCfgMode(mode);
      }
      break;
    case 3:
      SetSCfgModuloDivisor((uint32_t)record->val);
      break;
    case 4:
      SetSCfgModuloOffset((uint32_t)record->val);
      break;
    default:
      errlogSevPrintf(errlogFatal, "%s: record<<%s>>: ilegal signal\n"
        , __func__, record->name);
      status = -1;
  }

  return status;
}

/*************** longin ***************/

/* forward declarations */
long devSeqCtrlInitLongin(longinRecord *record);
long devSeqCtrlReadLongin(longinRecord *record);
long devSeqCtrlGetIointInfo(int cmd, struct dbCommon* com, IOSCANPVT *iospvt);

/* types */
typedef struct {
  long value;
  IOSCANPVT sio;
} LonginGlue;

typedef struct {
  QMActive * ao;
  int card;
  int signal;
  LonginGlue *glue;
} LonginPriv;

/* local objects */
static LonginGlue s_longin_glue[4];

/* global functions */
void SeqCtrl_SetIndex(uint32_t index) {
  s_longin_glue[0].value = (long) index;
  scanIoRequest(s_longin_glue[0].sio);
}

void SeqCtrl_SetLoad(long dummy) {
  s_longin_glue[1].value = dummy;
  scanIoRequest(s_longin_glue[1].sio);
}

void SeqCtrl_SetSop(long dummy) {
  s_longin_glue[2].value = dummy;
  scanIoRequest(s_longin_glue[2].sio);
}

void SeqCtrl_SetIsRunning(long is_running) {
  s_longin_glue[3].value = is_running;
  scanIoRequest(s_longin_glue[3].sio);
}

/* dset */
struct {
  long number;
  DEVSUPFUN report;
  DEVSUPFUN init;
  DEVSUPFUN init_record;
  DEVSUPFUN get_ioint_info;
  DEVSUPFUN read_longin;
} DevSeqCtrlLongin = {
  5,
  NULL,
  NULL,
  devSeqCtrlInitLongin,
  devSeqCtrlGetIointInfo,
  devSeqCtrlReadLongin
};
epicsExportAddress(dset, DevSeqCtrlLongin);

/* init */
long devSeqCtrlInitLongin(longinRecord *record) {
  LonginPriv *priv = NULL;

  TRACE_INFO(tp, ("%s #%s#: running", __func__, record->name));

  /* check arguments */
  if (record->inp.type != VME_IO) {
    errlogSevPrintf(errlogFatal, "%s #%s#: illegal INP link "
        "type\n", __func__, record->name);
    return -1;
  }
  switch (record->inp.value.vmeio.signal) {
    case 0:
    case 1:
    case 2:
    case 3:
      break;
    default:
      errlogSevPrintf(errlogFatal, "%s #%s#: invalid signal "
          "number %d\n", __func__, record->name,
          record->inp.value.vmeio.signal);
      return S_dev_badSignalNumber;
  }

  /* alloc memory */
  priv = malloc(sizeof(LonginPriv));
  if (!priv) {
    errlogSevPrintf(errlogFatal, "%s #%s#: out of memory\n", __func__,
        record->name);
    return S_dev_noMemory;
  }

  /* assign fields of private struct */
  priv->ao = AO_SeqCtrl;
  priv->card = record->inp.value.vmeio.card;
  priv->signal = record->inp.value.vmeio.signal; 
  switch (priv->signal) {
    case 0:
      priv->glue = &s_longin_glue[0];
      break;
    case 1:
      priv->glue = &s_longin_glue[1];
      break;
    case 2:
      priv->glue = &s_longin_glue[2];
      break;
    case 3:
      priv->glue = &s_longin_glue[3];
      break;
    default:
      errlogSevPrintf(errlogFatal, "%s #%s#: invalid signal "
          "number %d\n", __func__, record->name, priv->signal);
      return S_dev_badSignalNumber;
  }

  /* save private struct */
  record->dpvt = priv;

  return 0;
}

/* read */
long devSeqCtrlReadLongin(longinRecord *record) {
  int status = 0;
  LonginPriv *priv = (LonginPriv *) record->dpvt;

  TRACE_DEBUG(tp, ("%s #%s#: reading from C%d S%d",
        __func__, record->name, priv->card, priv->signal));

  /* check for init */
  if (!priv) {
    recGblSetSevr(record, UDF_ALARM, INVALID_ALARM);
    errlogSevPrintf(errlogFatal, "%s #%s#: record not initialized "
        "correctly\n", __func__, record->name);
    return -1;
  }

  /* get value */
  record->val = priv->glue->value;

  return status;
}

/* iointifo */
long  devSeqCtrlGetIointInfo(int cmd, struct dbCommon* com, IOSCANPVT *iospvt) {
  LonginPriv *priv = (LonginPriv *) com->dpvt;

  TRACE_INFO(tp, ("%s #%s#: running", __func__, com->name));

  /* check for init */
  if (!priv) {
    recGblSetSevr(com, UDF_ALARM, INVALID_ALARM);
    errlogSevPrintf(errlogFatal, "%s #%s#: record not initialized "
        "correctly\n", __func__, com->name);
    return -1;
  }

  /* provide IOSCANPVT */
  *iospvt = priv->glue->sio;

  return 0;
}

/***************** ai *****************/

/* forward declarations */
long devSeqCtrlInitAi(aiRecord *record);
long devSeqCtrlReadAi(aiRecord *record);
long devSeqCtrlGetIointInfoAi(int cmd, struct dbCommon* com, IOSCANPVT *iospvt);

/* types */
typedef struct {
  double value;
  IOSCANPVT sio;
} AiGlue;

typedef struct {
  int card;
  int signal;
  AiGlue *glue;
} AiPriv;

/* local objects */
static AiGlue s_ai_glue[1];

/* global functions */
void SeqCtrl_SetStartedAt(uint64_t pulseId) {
  TRACE_INFO(tp, ("%s running (pulseId=%" PRIu64 ")", __func__, pulseId));
  s_ai_glue[0].value = (double) pulseId;
  scanIoRequest(s_ai_glue[0].sio);
}

/* dset */
struct {
  long number;
  DEVSUPFUN report;
  DEVSUPFUN init;
  DEVSUPFUN init_record;
  DEVSUPFUN get_ioint_info;
  DEVSUPFUN read_ai;
  DEVSUPFUN special_linconv;
} DevSeqCtrlAi = {
  6,
  NULL,
  NULL,
  devSeqCtrlInitAi,
  devSeqCtrlGetIointInfoAi,
  devSeqCtrlReadAi,
  NULL
};
epicsExportAddress(dset, DevSeqCtrlAi);

/* init */
long devSeqCtrlInitAi(aiRecord *record) {
  long rv = 0;
  AiPriv *priv = NULL;
  
  TRACE_INFO(tp, ("%s #%s#: running", __func__, record->name));

  /* check arguments */
  if (record->inp.type != VME_IO) {
    errlogSevPrintf(errlogFatal, "%s #%s#: illegal INP link "
        "type\n", __func__, record->name);
    return -1;
  }
  switch (record->inp.value.vmeio.signal) {
    case 0:
      break;
    default:
      errlogSevPrintf(errlogFatal, "%s #%s#: invalid signal "
          "number %d\n", __func__, record->name,
          record->inp.value.vmeio.signal);
      return S_dev_badSignalNumber;
  }

  /* alloc memory */
  priv = malloc(sizeof(AiPriv));
  if (!priv) {
    errlogSevPrintf(errlogFatal, "%s #%s#: out of memory\n", __func__,
        record->name);
    return S_dev_noMemory;
  }

  /* assign fields of private struct */
  priv->card = record->inp.value.vmeio.card;
  priv->signal = record->inp.value.vmeio.signal; 
  switch (priv->signal) {
    case 0:
      priv->glue = &s_ai_glue[0];
      break;
    default:
      errlogSevPrintf(errlogFatal, "%s #%s#: invalid signal "
          "number %d\n", __func__, record->name, priv->signal);
      return S_dev_badSignalNumber;
  }

  /* save private struct */
  record->dpvt = priv;

  return rv;
}

/* read */
long devSeqCtrlReadAi(aiRecord *record) {
  long rv = 2; /* makes EPICS not call linear convert function */
  AiPriv *priv = (AiPriv *) record->dpvt;

  /* check for init */
  if (!priv) {
    recGblSetSevr(record, UDF_ALARM, INVALID_ALARM);
    errlogSevPrintf(errlogFatal, "%s #%s#: record not initialized "
        "correctly\n", __func__, record->name);
    return -1;
  }

  /* trace */
  TRACE_INFO(tp, ("%s #%s#: reading from C%d S%d, value=%f",
        __func__, record->name, priv->card, priv->signal, priv->glue->value));

  /* get value */
  record->val = priv->glue->value;

  return rv;
}

/* iointinfo */
long devSeqCtrlGetIointInfoAi(int cmd, struct dbCommon* com, IOSCANPVT *iospvt) {
  long rv = 0;
  AiPriv *priv = (AiPriv *) com->dpvt;

  /* check for init */
  if (!priv) {
    recGblSetSevr(com, UDF_ALARM, INVALID_ALARM);
    errlogSevPrintf(errlogFatal, "%s #%s#: record not initialized "
        "correctly\n", __func__, com->name);
    return -1;
  }

  /* trace */
  TRACE_INFO(tp, ("%s #%s#: running", __func__, com->name));

  /* provide IOSCANPVT */
  *iospvt = priv->glue->sio;

  return rv;
}

/**************** bo ******************/

/* forward declarations */
long devSeqCtrlInitBo(boRecord *record);
long devSeqCtrlWriteBo(boRecord *record);

/* interface with epics */
struct {
  long number;
  DEVSUPFUN report;
  DEVSUPFUN init;
  DEVSUPFUN init_record;
  DEVSUPFUN get_ioint_info;
  DEVSUPFUN write_bo;
} DevSeqCtrlBo = {
  5,
  NULL,
  NULL,
  devSeqCtrlInitBo,
  NULL,
  devSeqCtrlWriteBo
};
epicsExportAddress(dset, DevSeqCtrlBo);

/* init */
long devSeqCtrlInitBo(boRecord *record) {
  const char *param = NULL;

  TRACE_INFO(tp, ("%s: running for record %s", __func__, record->name));

  /* check arguments */
  if (record->out.type != INST_IO) {
    errlogSevPrintf(errlogFatal, "%s %s: illegal OUT link "
        "type\n", __func__, record->name);
    return -1;
  }

  /* setup signal */
  param = record->out.value.instio.string;
  if (strcmp(param, "START_SIG") == 0) record->dpvt = (void *) START_SIG;
  else if (strcmp(param, "STOP_SIG") == 0) record->dpvt = (void *) STOP_SIG;
  else if (strcmp(param, "SOP_SIG") == 0) record->dpvt = (void *) SOP_SIG;
  else {
    errlogSevPrintf(errlogFatal, "%s %s: invalid string parameter %s",
       __func__, record->name, record->out.value.instio.string);
    return -1;
  }

  return 0;
}

/* write */
long devSeqCtrlWriteBo(boRecord *record) {
  QEvent *evt = NULL;
  long signal = (long) record->dpvt;

  switch (signal) {
    case START_SIG:
    case STOP_SIG:
    case SOP_SIG:
      evt = Q_NEW(QEvt, signal);
      QACTIVE_POST(AO_SeqCtrl, evt, NULL);
      break;
  }

  return 0;
}

/************* init hooks *************/
static void DevSeqCtrlInitHook(initHookState state) {

  switch(state) {
    case initHookAtBeginning:
      TRACE_INFO(tp, ("%s: running for initHookAtBeginning", __func__));

      /* 0 index */
      scanIoInit(&s_longin_glue[0].sio);
      s_longin_glue[0].value = 0;     

      /* 1 load */
      scanIoInit(&s_longin_glue[1].sio);
      s_longin_glue[1].value = 0;     

      /* 2 SOP */
      scanIoInit(&s_longin_glue[2].sio);
      s_longin_glue[2].value = 0;     

      /* 3 IsRunning */
      scanIoInit(&s_longin_glue[3].sio);
      s_longin_glue[3].value = 0;     

      /* ai 0 StartAt */
      scanIoInit(&s_ai_glue[0].sio);
      s_ai_glue[0].value = 0;     

      break;
    default:
      break;
  }

}

/********** iocsh functions ***********/
static const iocshFuncDef dev_seq_ctrl_func_def = {"devSeqCtrlInit", 0, NULL};

static void DevSeqCtrlInit(const iocshArgBuf *args) {

  TRACE_INFO(tp, ("%s: running", __func__));

  initHookRegister(DevSeqCtrlInitHook);
  SeqCtrl_ctor();
}

static void DevSeqCtrlRegister() {

  iocshRegister(&dev_seq_ctrl_func_def, DevSeqCtrlInit);

}

epicsExportRegistrar(DevSeqCtrlRegister);

