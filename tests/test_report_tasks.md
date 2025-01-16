# Timing report
| start | duration | mpbuild | A | B | C |
| -: | -: | -: | -: | -: | -: |
| 0.0s | +3.5s | a | . | . | . |
| 3.5s | +7.5s | b | . | 1(a) | . |
| 11.0s | +1.0s | . | 2(b,c) | 1(a) | 2(b,c) |
| 12.0s | +0.5s | . | 2(b,c) | . | 2(b,c) |
| 12.5s | +2.0s | c | 2(b,c) | 3(b) | 2(b,c) |
| 14.5s | +0.5s | c | 4(b,c) | 3(b) | 4(b,c) |
| 15.0s | +3.0s | c | 4(b,c) | . | 4(b,c) |
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
| a | Build PICO2 |  | 3.5s |
| b | Build PICO2-RISCV |  | 7.5s |
| c | Build ESP8266 |  | 6.5s |
| 1 | Test X | PICO(PICO2) | 8.5s |
| 2 | Test Test X | PICO2(PICO2-RISCV), Lolin(ESP8266) | 3.5s |
| 3 | Test Y | PICO(PICO2-RISCV) | 2.5s |
| 4 | Test Test Y | PICO2(PICO2-RISCV), Lolin(ESP8266) | 3.5s |

## Report input data
| Start | End | Duration | Task | Tentacles |
| -: | -: | -: | :- | :- |
| 0.0s | 3.5s | 3.5s | Build PICO2 |  |
| 3.5s | 11.0s | 7.5s | Build PICO2-RISCV |  |
| 3.5s | 12.0s | 8.5s | Test X | PICO(PICO2) |
| 11.0s | 14.5s | 3.5s | Test Test X | PICO2(PICO2-RISCV), Lolin(ESP8266) |
| 12.5s | 15.0s | 2.5s | Test Y | PICO(PICO2-RISCV) |
| 12.5s | 19.0s | 6.5s | Build ESP8266 |  |
| 14.5s | 18.0s | 3.5s | Test Test Y | PICO2(PICO2-RISCV), Lolin(ESP8266) |
