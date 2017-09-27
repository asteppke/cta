
#include "tracing.h"
#include "seqCtrl.h"

#include <devSup.h>
#include <aoRecord.h>
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

/* tracing */
static int devSeqCtrlTraceLevel = TRACE_LEVEL_NONE;
static TracePoint tp = {&devSeqCtrlTraceLevel, "devSeqCtrl"};

/********** analog output **********/

/* forward declarations */
long DevSeqCtrlInitAo(aoRecord *record);
long DevSeqCtrlWriteAo(aoRecord *record);

/* device support for ao */
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

long DevSeqCtrlInitAo(aoRecord *record) {
  #if 0
  SedePrivate *priv;
  epicsUInt16 initval;
  SedeCard *card;
  int signal;
  #endif

  TRACE_INFO(tp, ("%s: running for record %s", __func__, record->name));

#if 0
  /* check arguments */
  if (record->out.type != VME_IO) {
    errlogSevPrintf(errlogFatal, "DevSeqCtrlInitAo %s: illegal OUT link type\n"
        , record->name);
    return -1;
  }
  signal = record->out.value.vmeio.signal;
  if (signal < 0 || signal >= 8) {
    errlogSevPrintf(errlogFatal, "DevSeqCtrlInitAo %s: invalid signal number "
        "%d\n", record->name, signal);
    return S_dev_badSignalNumber;
  }

  /* open */
  card = SedeOpen(record->out.value.vmeio.card);
  if (!card) {
    errlogSevPrintf(errlogFatal,
        "DevSeqCtrlInitAo %s: invalid card number %i\n",
        record->name, record->out.value.vmeio.card);
    return S_dev_noDevice;
  }

  /* alloc memory */
  priv = (SedePrivate *) malloc(sizeof(SedePrivate));
  if (!priv) {
    errlogSevPrintf(errlogFatal, "DevSeqCtrlInitAo %s: out of memory\n",
        record->name);
    return S_dev_noMemory;
  }
  priv->card = card;
  priv->signal = signal;
  record->dpvt = priv;

  /* init */
  DevSeqCtrlLinconvAo(record, TRUE);
  SedeGet(card, signal, &initval);
  record->rval = (epicsInt32) initval;

#endif

  return 0;
}

/*---------------------------------------------------------------------------*/
long DevSeqCtrlWriteAo(aoRecord *record) {
  /* SedePrivate *priv = (SedePrivate *) record->dpvt; */
  int status = 0;
  StartOfSeq *evt = NULL;

  TRACE_DEBUG(tp, ("%s: record <<%s>> writes to C%d S%d",
        __func__, record->name, record->out.value.vmeio.card,
        record->out.value.vmeio.signal));


  evt = Q_NEW(StartOfSeq, SOS_SIG);
  evt->pulse_id = (uint64_t) record->val;
  QACTIVE_POST(AO_SeqCtrl, &evt->super, NULL);

  #if 0
  /* check for init */
  if (!priv) {
    recGblSetSevr(record, UDF_ALARM, INVALID_ALARM);
    errlogSevPrintf(errlogFatal, "DevSeqCtrlWriteAo %s: record not initialized "
        "correctly\n", record->name);
    return -1;
  }

  /* write */
  status = SedeSet(priv->card, priv->signal, (epicsUInt16) record->rval);
  if (status) {
    errlogSevPrintf(errlogFatal, "DevSeqCtrlWriteAo %s: SedeSet failed: error "
        "code 0x%x\n", record->name, status);
    recGblSetSevr(record, WRITE_ALARM, INVALID_ALARM);
  }


  #endif

  return status;
}

/************************************** longout *******************************/

/* forward declarations */
long devSeqCtrlInitLongout(longoutRecord *record);
long devSeqCtrlWriteLongout(longoutRecord *record);

/* device support for longout */
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

/*---------------------------------------------------------------------------*/
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

/*---------------------------------------------------------------------------*/
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
    default:
      errlogSevPrintf(errlogFatal, "%s: record<<%s>>: ilegal signal\n"
        , __func__, record->name);
      status = -1;
  }

  return status;
}


/************************************** longin ********************************/

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
static LonginGlue s_longin_glue[3];

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

/* device support for longin */
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

/*---------------------------------------------------------------------------*/
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
    default:
      errlogSevPrintf(errlogFatal, "%s #%s#: invalid signal "
          "number %d\n", __func__, record->name, priv->signal);
      return S_dev_badSignalNumber;
  }

  /* save private struct */
  record->dpvt = priv;

  return 0;
}

/*----------------------------------------------------------------------------*/
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

/*----------------------------------------------------------------------------*/
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

/************************************** bo ************************************/

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

/*---------------------------------------------------------------------------*/
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

/*---------------------------------------------------------------------------*/
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

/****************** init hooks ************************************************/
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

      break;
    default:
      break;
  }

}

/****************** iocsh functions *******************************************/
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

