# Timing report
| start | duration | mpbuild | A | B | C |
| -: | -: | -: | -: | -: | -: |
| 0.0s | +3.2s | a | . | . | . |
| 3.2s | +0.2s | . | . | . | . |
| 3.4s | +7.4s | b | . | 1(a) | . |
| 10.8s | +0.2s | . | . | 1(a) | . |
| 11.0s | +1.2s | . | 2(b,c) | 1(a) | 2(b,c) |
| 12.2s | +0.2s | . | 2(b,c) | 3(b) | 2(b,c) |
| 12.4s | +1.8s | c | 2(b,c) | 3(b) | 2(b,c) |
| 14.2s | +0.2s | c | . | 3(b) | . |
| 14.4s | +0.8s | c | 4(b,c) | 3(b) | 4(b,c) |
| 15.2s | +2.8s | c | 4(b,c) | . | 4(b,c) |
| 18.0s | +1.0s | c | . | . | . |
| 19.0s |  | . | . | . | . |

## Legend: Tentacles
| Tentacle-ID | Tentacles |
| -: | :- |
| mpbuild | mpbuild |
| A | Lolin |
| B | PICO |
| C | PICO2 |

## Legend: Tasks
| Task-ID | Task | Tentacle | Duration |
| -: | :- | :- | -: |
| a | Build PICO2 |  | 3.2s |
| b | Build PICO2-RISCV |  | 7.4s |
| 1 | Test X | PICO(PICO2) | 8.8s |
| 2 | Test Test X | PICO2(PICO2-RISCV), Lolin(ESP8266) | 3.2s |
| 3 | Test Y | PICO(PICO2-RISCV) | 3.0s |
| c | Build ESP8266 |  | 6.6s |
| 4 | Test Test Y | PICO2(PICO2-RISCV), Lolin(ESP8266) | 3.6s |

## Report input data
| Start | End | Duration | Task | Tentacles |
| -: | -: | -: | :- | :- |
| 0.0s | 3.2s | 3.2s | Build PICO2 |  |
| 3.4s | 10.8s | 7.4s | Build PICO2-RISCV |  |
| 3.4s | 12.2s | 8.8s | Test X | PICO(PICO2) |
| 11.0s | 14.2s | 3.2s | Test Test X | PICO2(PICO2-RISCV), Lolin(ESP8266) |
| 12.2s | 15.2s | 3.0s | Test Y | PICO(PICO2-RISCV) |
| 12.4s | 19.0s | 6.6s | Build ESP8266 |  |
| 14.4s | 18.0s | 3.6s | Test Test Y | PICO2(PICO2-RISCV), Lolin(ESP8266) |
