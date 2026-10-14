// update_adc_phase.cpp: calls the C++ reader's ExternalSequence::updateAdcPhaseModulation.
//
//   update_adc_phase FILE ox oy oz
//
// Loads FILE with ExternalSequence::load, prints the ADC phase shape of block 0, the gradients
// (SeqBlock::gradientsAt) and the gradient moments (SeqBlock::gradMomentsAt) of block 0 at the
// ADC sample centres, then calls updateAdcPhaseModulation with the position offset (ox, oy, oz)
// in mm and the gradient scaling (1, 1, 1), and prints the new ADC phase shape of block 0.
//
// Build against src/ of pulseq/pulseq c7469123 (C++11: the reader uses std::bind1st):
//   clang++ -std=c++11 -fsigned-char -ffp-contract=off -I<pulseq>/src -o update_adc_phase \
//     update_adc_phase.cpp <pulseq>/src/ExternalSequence.cpp <pulseq>/src/md5.cpp
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <string>
#include "ExternalSequence.h"
static void to_stderr(const std::string& m) { fprintf(stderr, "%s\n", m.c_str()); }
static void print_shape(ExternalSequence& s, const char* tag) {
  SeqBlock* b = s.GetBlock(0);
  const ADCEvent& a = b->GetADCEvent();
  printf("%s: adc phase shape id %d:", tag, a.phaseModulationShapeID);
  if (a.phaseModulationShapeID > 0) {
    std::vector<float> v;
    s.getDecompressedShapeForID(a.phaseModulationShapeID, v);
    for (float x : v) printf(" %.6f", x);
  }
  printf("\n");
  delete b;
}
int main(int argc, char** argv) {
  if (argc != 5) return 2;
  ExternalSequence::SetPrintFunction(&to_stderr);
  ExternalSequence s;
  if (!s.load(argv[1])) { printf("load failed\n"); return 1; }
  print_shape(s, "before");
  SeqBlock* b = s.GetBlock(0);
  s.decodeBlock(b);
  printf("rotation: %d", (int)b->isRotation());
  if (b->isRotation()) { double* q = b->GetRotationEvent().rotQuaternion; printf(" q = %g %g %g %g", q[0], q[1], q[2], q[3]); }
  printf("\n");
  for (int k = 0; k < 10; ++k) {
    double t = (k + 0.5) * 10.0;
    std::vector<double> g; b->gradientsAt(t, g);
    std::vector<double> m; b->gradMomentsAt(t, m);
    printf("t=%5.1f us grad = %10.2f %10.2f %10.2f  moment = %10.1f %10.1f %10.1f\n", t, g[0], g[1], g[2], m[0], m[1], m[2]);
  }
  delete b;
  std::vector<double> off = {atof(argv[2]), atof(argv[3]), atof(argv[4])}, sc = {1, 1, 1};
  int n = s.updateAdcPhaseModulation(off, sc);
  printf("updateAdcPhaseModulation(%g, %g, %g) mm returned %d\n", off[0], off[1], off[2], n);
  print_shape(s, "after");
  return 0;
}
