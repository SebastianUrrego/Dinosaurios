# Muestreo

Modelo: **B: GRU 2x256**. 200 nombres por estrategia (semilla 7).

- **nuevos %**: nombres de 4 o más letras que no están en `dinos.csv`.
- **sufijo real %**: terminan en un sufijo frecuente de dinosaurios reales (saurus, raptor, odon, venator, don, ops, rex, mimus, titan, ceratops).

| Estrategia | nuevos % | únicos % | long. media | sufijo real % | ejemplos |
|---|---|---|---|---|---|
| T = 0.5 | 87.0 | 92.5 | 11.8 | 78.0 | Madrosaurus, Laphorhinis, Raivenator, Tangnasaurus, Comadia |
| T = 1.0 | 99.0 | 100.0 | 12.0 | 57.5 | Nexingxaura, Nesenosaurus, Laowlangodon, Siljiafelisaurus, Ubisteosaurus |
| T = 1.5 | 97.0 | 98.5 | 12.5 | 30.0 | Nexinixaips, Nmsendutliavenlonlyus, Dhproilosaurus, Porntaudisteosuchus, Hixirnkusaurus |
| top-k = 5 (T = 1.0) | 93.0 | 97.5 | 12.0 | 68.5 | Tenganthongosaurus, Chingosaurus, Protyoraptor, Steosuchus, Sinirosaurus |
| top-p = 0.9 (T = 1.0) | 96.5 | 100.0 | 11.9 | 71.5 | Nexingxaura, Nesenosaurus, Laowanlius, Proptoraptor, Parataceratops |

## Diez nombres (top-p = 0.9 (T = 1.0))

1. Ereidasaurus
2. Crothongosaurus
3. Coratosaurus
4. Deistavuraptor
5. Dyrotaphalus
6. Pispondylus
7. Aborosaurus
8. Hopalophosaurus
9. Taivelasaurus
10. Alticoelia
