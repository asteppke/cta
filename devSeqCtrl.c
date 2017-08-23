
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

#include <string.h>

/* tracing */
static int devSeqCtrlTraceLevel = TRACE_LEVEL_DEBUG;
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
IOSCANPVT index_scanio;

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
  /* SedePrivate *priv; */
  /* epicsUInt16 initval; */
  /* SedeCard *card; */
  /* int signal; */

  TRACE_INFO(tp, ("%s: running for record %s", __func__, record->name));

  /* check arguments */
  if (record->inp.type != VME_IO) {
    errlogSevPrintf(errlogFatal, "devSeqCtrlInitLongin %s: illegal OUT link "
        "type\n", record->name);
    return -1;
  }

  /* init i/o scanning */
  scanIoInit(&index_scanio);

#if 0
  signal = record->inp.value.vmeio.signal;
  if (signal < 0 || signal >= 8) {
    errlogSevPrintf(errlogFatal, "SedeInitLongin %s: invalid signal "
        "number %d\n", record->name, signal);
    return S_dev_badSignalNumber;
  }

  /* open */
  card = SedeOpen(record->inp.value.vmeio.card);
  if (!card) {
    errlogSevPrintf(errlogFatal, "SedeInitLongin %s: invalid card number"
       " %i\n", record->name, record->inp.value.vmeio.card);
    return S_dev_noDevice;
  }

  /* alloc memory */
  priv = (SedePrivate *) malloc(sizeof(SedePrivate));
  if (!priv) {
    errlogSevPrintf(errlogFatal, "SedeInitLongin %s: out of memory\n",
        record->name);
    return S_dev_noMemory;
  }
  priv->card = card;
  priv->signal = signal;
  record->dpvt = priv;

  /* init */
  SedeGet(card, signal, &initval);
  record->val = (epicsInt32) initval;
#endif

  return 0;
}

/*---------------------------------------------------------------------------*/
long devSeqCtrlReadLongin(longinRecord *record) {
  int status = 0;

  TRACE_DEBUG(tp, ("%s: record <<%s>> reads from C%d S%d",
        __func__, record->name, record->inp.value.vmeio.card,
        record->inp.value.vmeio.signal));

#if 0
  /* check for init */
  if (!priv) {
    recGblSetSevr(record, UDF_ALARM, INVALID_ALARM);
    errlogSevPrintf(errlogFatal, "SedeReadLongin %s: record not initialized "
        "correctly\n", record->name);
    return -1;
  }

  /* read */
  {
    epicsUInt16 value;

    status = SedeGet(priv->card, priv->signal, &value);
    if (status) {
      errlogSevPrintf(errlogFatal, "SedeReadLongin %s: SedeGet failed: error "
          "code 0x%x\n", record->name, status);
      recGblSetSevr(record, READ_ALARM, INVALID_ALARM);
    }
    record->val = (epicsInt32) value;
  }
#endif

  record->val = (epicsInt32) GetIndex();

  return status;
}

long  devSeqCtrlGetIointInfo(int cmd, struct dbCommon* com, IOSCANPVT *iospvt) {

  TRACE_INFO(tp, ("%s: running for record %s", __func__, com->name));

  /* provide IOSCANPVT */
  *iospvt = index_scanio;

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
    case SOS_SIG:
      evt = Q_NEW(QEvt, signal);
      QACTIVE_POST(AO_SeqCtrl, evt, NULL);
      break;
  }

  return 0;
}

