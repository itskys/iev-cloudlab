#include <stdlib.h>
#include <math.h>
#include "fmi2Functions.h"

#define VR_P_ELEC 0
#define VR_SOC 1
#define VR_V_TERM 2
#define VR_Q_AH 3

typedef struct {
    fmi2Real P_elec;
    fmi2Real soc;
    fmi2Real V_term;
    fmi2Real Q_Ah;
    fmi2Real R0;
} Model;

static fmi2Real ocv(fmi2Real soc) { return 3.0 + 1.2 * soc; }

FMI2_Export const char* fmi2GetTypesPlatform(void) { return fmi2TypesPlatform; }
FMI2_Export const char* fmi2GetVersion(void) { return fmi2Version; }

FMI2_Export fmi2Component fmi2Instantiate(fmi2String id, fmi2Type type, fmi2String guid,
    fmi2String res, const fmi2CallbackFunctions* cb, fmi2Boolean vis, fmi2Boolean log) {
    Model* m = (Model*)calloc(1, sizeof(Model));
    m->soc = 0.8; m->Q_Ah = 50.0; m->R0 = 0.05;
    m->V_term = ocv(m->soc);
    return m;
}
FMI2_Export void fmi2FreeInstance(fmi2Component c) { free(c); }
FMI2_Export fmi2Status fmi2SetupExperiment(fmi2Component c, fmi2Boolean tol,
    fmi2Real t, fmi2Real t0, fmi2Boolean stop, fmi2Real stopT) { return fmi2OK; }
FMI2_Export fmi2Status fmi2EnterInitializationMode(fmi2Component c) { return fmi2OK; }
FMI2_Export fmi2Status fmi2ExitInitializationMode(fmi2Component c) { return fmi2OK; }
FMI2_Export fmi2Status fmi2Terminate(fmi2Component c) { return fmi2OK; }
FMI2_Export fmi2Status fmi2Reset(fmi2Component c) {
    Model* m = (Model*)c; m->soc = 0.8; m->P_elec = 0; m->V_term = ocv(m->soc); return fmi2OK;
}
FMI2_Export fmi2Status fmi2GetReal(fmi2Component c, const fmi2ValueReference vr[], size_t n, fmi2Real v[]) {
    Model* m = (Model*)c;
    for (size_t i = 0; i < n; i++) {
        if (vr[i] == VR_SOC) v[i] = m->soc;
        else if (vr[i] == VR_V_TERM) v[i] = m->V_term;
        else if (vr[i] == VR_P_ELEC) v[i] = m->P_elec;
        else return fmi2Error;
    }
    return fmi2OK;
}
FMI2_Export fmi2Status fmi2SetReal(fmi2Component c, const fmi2ValueReference vr[], size_t n, const fmi2Real v[]) {
    Model* m = (Model*)c;
    for (size_t i = 0; i < n; i++) {
        if (vr[i] == VR_P_ELEC) m->P_elec = v[i];
        else if (vr[i] == VR_Q_AH) m->Q_Ah = v[i];
        else return fmi2Error;
    }
    return fmi2OK;
}
FMI2_Export fmi2Status fmi2DoStep(fmi2Component c, fmi2Real t, fmi2Real dt, fmi2Boolean noSetFMUState) {
    Model* m = (Model*)c;
    fmi2Real I = (m->V_term > 1.0) ? m->P_elec / m->V_term : 0.0;
    m->soc -= dt * I / (m->Q_Ah * 3600.0);
    if (m->soc < 0) m->soc = 0; if (m->soc > 1) m->soc = 1;
    m->V_term = ocv(m->soc) - I * m->R0;
    return fmi2OK;
}
FMI2_Export fmi2Status fmi2CancelStep(fmi2Component c) { return fmi2OK; }
