# BTC-SPOT-E2-20261013 — registrazione prima dei risultati

E1 è concluso come screening: 72 configurazioni; nessuna raggiunge il minimo di 50 operazioni determinate nello sviluppo 2020–2022. I risultati E1 non vengono cancellati e il 2025 non è stato valutato.

E2 mantiene integralmente protocollo, famiglie, target, invalidazione, orizzonti, costi, split cronologico, cooldown, controlli qualità e minimi campionari di E1. L'unica espansione è la soglia di movimento normalizzato: **1,5 e 2,0**, anziché 2,5. Non aggiunge indicatori, non cambia i minimi per far passare un candidato e non usa il 2025 per scegliere le soglie.

Sono previste 144 configurazioni aggiuntive (2 soglie × 6 famiglie × 3 durate × 2 target × 2 direzioni). I 72 tentativi E1 restano parte del conteggio: 216 configurazioni complessive prima dell'eventuale holdout.

Selezione E2: per ciascuna direzione, tra i modelli con almeno 50 trade determinati nello sviluppo e 30 nella validazione, scegliere il maggiore rendimento logaritmico medio netto della validazione 2023–2024. Pareggi: soglia, famiglia, durata, target in ordine crescente. Non qualificare automaticamente un risultato positivo: restano tutti i gate del protocollo E1, inclusa positività nello sviluppo, entrambi gli anni di validazione, numerosità e limite inferiore bootstrap nel holdout, stress dei costi e assenza di piani indeterminati nel holdout.

La baseline fissa E2 è: soglia 2,0; famiglia shock; durata 48h; target 1 sigma giornaliera, invalidazione 1 sigma. Le uniche configurazioni E2 ammesse all'osservazione finale del 2025 sono questa baseline e l'eventuale candidato selezionato per ciascuna direzione. Non ritoccare nulla dopo quel test.

Il protocollo JSON E2 completo è stato scritto localmente prima dell'analisi. SHA-256: `7f240f2707d4fd8d84dfcd3c3115b99426b83b262dab804b7b75f7ab891631b5`.

Il protocollo E1 di riferimento è `protocol.json`, SHA-256 `9d4be8b5cd03e2950d449236ad50af7b37dadab1a59a877e6ec8b3a994d44b29`, già congelato su GitHub. Un campione troppo piccolo o un risultato negativo limita questa ipotesi, non dimostra che ogni possibile strategia sia inefficace.
