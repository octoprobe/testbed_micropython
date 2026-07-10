# Timing report
| start | duration | mpbuild | A |
| -: | -: | -: | -: |
| 0.0s | +61.5s | a | . |
| 61.5s | +15.0s | b | 1(a) |
| 76.5s | +23.0s | b | . |
| 99.5s | +15.5s | . | 2(b) |
| 115.0s |  | . | . |

## Legend: Tentacles
| Tentacle-ID | Tentacles |
| -: | :- |
| mpbuild | mpbuild |
| A | 5334-RPI\_PICO2 |

## Legend: Tasks
| Task-ID | Task | Tentacle | Duration |
| -: | :- | :- | -: |
| a | Build RPI\_PICO2 |  | 61.5s |
| b | Build RPI\_PICO2-RISCV |  | 38.0s |
| 1 | Test RUN-TESTS\_EXTMOD\_HARDWARE@5334-RPI\_PICO2 | 5334-RPI\_PICO2(RPI\_PICO2) | 15.0s |
| 2 | Test RUN-TESTS\_EXTMOD\_HARDWARE@5334-RPI\_PICO2-RISCV | 5334-RPI\_PICO2(RPI\_PICO2-RISCV) | 15.5s |

## Report input data
| Start | End | Duration | Task | Tentacles |
| -: | -: | -: | :- | :- |
| 0.0s | 61.5s | 61.5s | Build RPI\_PICO2 |  |
| 61.5s | 76.5s | 15.0s | Test RUN-TESTS\_EXTMOD\_HARDWARE@5334-RPI\_PICO2 | 5334-RPI\_PICO2(RPI\_PICO2) |
| 61.5s | 99.5s | 38.0s | Build RPI\_PICO2-RISCV |  |
| 99.5s | 115.0s | 15.5s | Test RUN-TESTS\_EXTMOD\_HARDWARE@5334-RPI\_PICO2-RISCV | 5334-RPI\_PICO2(RPI\_PICO2-RISCV) |
