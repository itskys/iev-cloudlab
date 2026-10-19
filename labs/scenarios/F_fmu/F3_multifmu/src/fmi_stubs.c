/* Stub implementations of optional FMI 2.0 functions required by FMPy */
#include "fmi2Functions.h"

FMI2_Export fmi2Status fmi2SetDebugLogging(fmi2Component c, fmi2Boolean loggingOn,
    size_t nCategories, const fmi2String categories[]) { return fmi2OK; }
FMI2_Export fmi2Status fmi2GetDirectionalDerivative(fmi2Component c,
    const fmi2ValueReference vUnknownRef[], size_t nUnknown,
    const fmi2ValueReference vKnownRef[], size_t nKnown,
    const fmi2Real dvKnown[], fmi2Real dvUnknown[]) { return fmi2Discard; }
FMI2_Export fmi2Status fmi2SetRealInputDerivatives(fmi2Component c,
    const fmi2ValueReference vr[], size_t n, const fmi2Integer order[], const fmi2Real value[]) { return fmi2OK; }
FMI2_Export fmi2Status fmi2GetRealOutputDerivatives(fmi2Component c,
    const fmi2ValueReference vr[], size_t n, const fmi2Integer order[], fmi2Real value[]) { return fmi2Discard; }
FMI2_Export fmi2Status fmi2GetFMUstate(fmi2Component c, fmi2FMUstate* s) { return fmi2Discard; }
FMI2_Export fmi2Status fmi2SetFMUstate(fmi2Component c, fmi2FMUstate s) { return fmi2Discard; }
FMI2_Export fmi2Status fmi2FreeFMUstate(fmi2Component c, fmi2FMUstate* s) { return fmi2OK; }
FMI2_Export fmi2Status fmi2SerializedFMUstateSize(fmi2Component c, fmi2FMUstate s, size_t* size) { return fmi2Discard; }
FMI2_Export fmi2Status fmi2SerializeFMUstate(fmi2Component c, fmi2FMUstate s, fmi2Byte data[], size_t size) { return fmi2Discard; }
FMI2_Export fmi2Status fmi2DeSerializeFMUstate(fmi2Component c, const fmi2Byte data[], size_t size, fmi2FMUstate* s) { return fmi2Discard; }
FMI2_Export fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t n, fmi2Integer v[]) { return fmi2Error; }
FMI2_Export fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t n, fmi2Boolean v[]) { return fmi2Error; }
FMI2_Export fmi2Status fmi2GetString(fmi2Component c, const fmi2ValueReference vr[], size_t n, fmi2String v[]) { return fmi2Error; }
FMI2_Export fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t n, const fmi2Integer v[]) { return fmi2Error; }
FMI2_Export fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t n, const fmi2Boolean v[]) { return fmi2Error; }
FMI2_Export fmi2Status fmi2SetString(fmi2Component c, const fmi2ValueReference vr[], size_t n, const fmi2String v[]) { return fmi2Error; }
/* Status queries */
FMI2_Export fmi2Status fmi2GetStatus(fmi2Component c, const fmi2StatusKind s, fmi2Status* v) { return fmi2Discard; }
FMI2_Export fmi2Status fmi2GetRealStatus(fmi2Component c, const fmi2StatusKind s, fmi2Real* v) { return fmi2Discard; }
FMI2_Export fmi2Status fmi2GetIntegerStatus(fmi2Component c, const fmi2StatusKind s, fmi2Integer* v) { return fmi2Discard; }
FMI2_Export fmi2Status fmi2GetBooleanStatus(fmi2Component c, const fmi2StatusKind s, fmi2Boolean* v) { return fmi2Discard; }
FMI2_Export fmi2Status fmi2GetStringStatus(fmi2Component c, const fmi2StatusKind s, fmi2String* v) { return fmi2Discard; }
FMI2_Export fmi2Status fmi2CompletedIntegratorStep(fmi2Component c, fmi2Boolean noSetFMUState, fmi2Boolean* enterEventMode, fmi2Boolean* terminateSimulation) { return fmi2OK; }
/* Model Exchange stubs (not used in CS, but FMPy looks them up) */
FMI2_Export fmi2Status fmi2EnterEventMode(fmi2Component c) { return fmi2OK; }
FMI2_Export fmi2Status fmi2NewDiscreteStates(fmi2Component c, fmi2EventInfo* e) { return fmi2OK; }
FMI2_Export fmi2Status fmi2EnterContinuousTimeMode(fmi2Component c) { return fmi2OK; }
FMI2_Export fmi2Status fmi2SetTime(fmi2Component c, fmi2Real t) { return fmi2OK; }
FMI2_Export fmi2Status fmi2SetContinuousStates(fmi2Component c, const fmi2Real x[], size_t n) { return fmi2OK; }
FMI2_Export fmi2Status fmi2GetDerivatives(fmi2Component c, fmi2Real d[], size_t n) { return fmi2Discard; }
FMI2_Export fmi2Status fmi2GetEventIndicators(fmi2Component c, fmi2Real z[], size_t n) { return fmi2Discard; }
FMI2_Export fmi2Status fmi2GetContinuousStates(fmi2Component c, fmi2Real x[], size_t n) { return fmi2Discard; }
FMI2_Export fmi2Status fmi2GetNominalsOfContinuousStates(fmi2Component c, fmi2Real x[], size_t n) { return fmi2Discard; }
