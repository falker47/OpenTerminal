# E2 — selezione congelata prima del test 2025

Il 2025 non è stato valutato. Questa selezione segue E2_PREREGISTRATION.md; nessun parametro verrà cambiato dopo la lettura del holdout.

144 configurazioni E2, più 72 E1 conservate: 216 tentativi complessivi.

## SELL -> BUY
- Soglia shock normalizzato: 1,5.
- Famiglia: slowdown_flow (rallentamento + riduzione della pressione direzionale taker).
- Orizzonte massimo: 48 ore.
- Target: 0,5 sigma giornaliera; invalidazione: 1,0 sigma.
- Sviluppo 2020–2022: 65 trade determinati; rendimento medio netto in quantità BTC -0,322526%.
- Validazione 2023–2024: 63 trade determinati e 1 indeterminato; media netta -0,075001%; 68,253968% dei trade determinati positivi.
- Migliore tra i candidati con numerosità ammessa, **non candidato operativo**: risultato negativo nello sviluppo e nella validazione aggregata. Il 2023 è negativo; il 2024 è positivo.

## BUY -> SELL
- Soglia shock normalizzato: 1,5.
- Famiglia: shock (nessun filtro aggiuntivo).
- Orizzonte massimo: 72 ore.
- Target: 0,5 sigma giornaliera; invalidazione: 1,0 sigma.
- Sviluppo 2020–2022: 74 trade determinati; rendimento medio netto in valuta quotata -0,227188%.
- Validazione 2023–2024: 66 trade determinati; media netta +0,186853%; 78,787879% dei trade positivi.
- Migliore tra i candidati con numerosità ammessa, **non candidato operativo**: sviluppo negativo; media 2023 +0,477491%, media 2024 -0,070568%.

## Baseline e interpretazione del test finale

Baseline fissa per entrambe le direzioni: shock soglia 2,0, orizzonte 48h, target 1,0 sigma, invalidazione 1,0 sigma.

Solo baseline e selezionato per direzione sono valutati nel 2025. Il test finale è diagnostico: nessun esito 2025 può cancellare i gate già falliti nello sviluppo/validazione. Un trade positivo non implica che la strategia abbia aspettativa positiva.

Costi base per ogni lato: commissione 0,1%, slippage 0,05%; imposte escluse. Soglie, benchmark e formule complete nel protocollo. Dati: Binance Spot BTCUSDT orari; nessun saldo personale.

## Identificativi riproducibili

- Dataset CSV SHA-256: `de110de0333525d14b46c287fc7fe20a1353ea2e40fcb5710c7c78ac13e590da`.
- Protocollo E2 SHA-256: `7f240f2707d4fd8d84dfcd3c3115b99426b83b262dab804b7b75f7ab891631b5`.
- Motore study.py SHA-256: `35b860510e11629291eb424df4e03f72dd150fc5bea4dae62198040a1192312f`.
- Runner E2 SHA-256: `00de100d6f6ed9fc78392e16b762852ba5021a555833e55df0f0e2d9933b6bea`.

La selezione JSON completa viene conservata tra gli artefatti della ricerca. Nessun segnale live o strategia validata è dichiarato.
