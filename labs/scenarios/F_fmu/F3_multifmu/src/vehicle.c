#include <stdlib.h>
#include <math.h>
#include "fmi2Functions.h"

#define VR_F_MOTOR 0
#define VR_V 1
#define VR_X 2
#define VR_MASS 3

typedef struct {
    fmi2Real F_motor;
    fmi2Real v, x;
    fmi2Real mass;
    fmi2Real Cd, A, rho, Crr, g;
} Model;

FMI2_Export const char* fmi2GetTypesPlatform(void) { return fmi2TypesPlatform; }
FMI2_Export const char* fmi2GetVersion(void) { return fmi2Version; }

FMI2_Export fmi2Component fmi2Instantiate(fmi2String id, fmi2Type type, fmi2String guid,
    fmi2String res, const fmi2CallbackFunctions* cb, fmi2Boolean vis, fmi2Boolean log) {
    Model* m = (Model*)calloc(1, sizeof(Model));
    m->mass = 1500.0; m->Cd = 0.28; m->A = 2.2; m->rho = 1.225; m->Crr = 0.01; m->g = 9.81;
    return m;
}
FMI2_Export void fmi2FreeInstance(fmi2Component c) { free(c); }
FMI2_Export fmi2Status fmi2SetupExperiment(fmi2Component c, fmi2Boolean tol,
    fmi2Real t, fmi2Real t0, fmi2Boolean stop, fmi2Real stopT) { return fmi2OK; }
FMI2_Export fmi2Status fmi2EnterInitializationMode(fmi2Component c) { return fmi2OK; }
FMI2_Export fmi2Status fmi2ExitInitializationMode(fmi2Component c) { return fmi2OK; }
FMI2_Export fmi2Status fmi2Terminate(fmi2Component c) { return fmi2OK; }
FMI2_Export fmi2Status fmi2Reset(fmi2Component c) {
    Model* m = (Model*)c; m->v = 0; m->x = 0; m->F_motor = 0; return fmi2OK;
}
FMI2_Export fmi2Status fmi2GetReal(fmi2Component c, const fmi2ValueReference vr[], size_t n, fmi2Real v[]) {
    Model* m = (Model*)c;
    for (size_t i = 0; i < n; i++) {
        if (vr[i] == VR_V) v[i] = m->v;
        else if (vr[i] == VR_X) v[i] = m->x;
        else if (vr[i] == VR_F_MOTOR) v[i] = m->F_motor;
        else return fmi2Error;
    }
    return fmi2OK;
}
FMI2_Export fmi2Status fmi2SetReal(fmi2Component c, const fmi2ValueReference vr[], size_t n, const fmi2Real v[]) {
    Model* m = (Model*)c;
    for (size_t i = 0; i < n; i++) {
        if (vr[i] == VR_F_MOTOR) m->F_motor = v[i];
        else if (vr[i] == VR_MASS) m->mass = v[i];
        else return fmi2Error;
    }
    return fmi2OK;
}
FMI2_Export fmi2Status fmi2DoStep(fmi2Component c, fmi2Real t, fmi2Real dt, fmi2Boolean noSetFMUState) {
    Model* m = (Model*)c;
    fmi2Real F_drag = 0.5 * m->rho * m->Cd * m->A * m->v * fabs(m->v);
    fmi2Real F_rr = m->mass * m->g * m->Crr * (m->v >= 0 ? 1 : -1);
    fmi2Real a = (m->F_motor - F_drag - F_rr) / m->mass;
    m->v += a * dt;
    if (m->v < 0) m->v = 0;
    m->x += m->v * dt;
    return fmi2OK;
}
FMI2_Export fmi2Status fmi2CancelStep(fmi2Component c) { return fmi2OK; }
