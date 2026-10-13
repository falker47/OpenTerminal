# BTC Spot — anomalie, spiegazioni e piani operativi

Stato: **SPECIFICA REVISIONATA DA APPROVARE — NON IMPLEMENTATA, NESSUNA STRATEGIA VALIDATA**.
Revisione: 2, 13 ottobre 2026.
Repository: `falker47/OpenTerminal`.
Baseline applicativa riletta: `aed097c680cd8ec1c391ae06966babe7d6d91fc6`.
Branch documentale: `docs/btc-spot-mvp-design`.
Upstream: `ErTasselli/OpenTerminal`; licenza e attribuzioni restano inalterate.

## 1. Correzione del requisito

La revisione del 13 ottobre sostituisce la proposta del simulatore manuale. Il prodotto deve osservare il mercato e individuare un evento anomalo quando si verifica, spiegarne le evidenze e proporre se vendere, acquistare o attendere, associando all'eventuale operazione un target per l'operazione opposta, un orizzonte temporale e condizioni d'invalidazione.

La domanda centrale è: «È successo qualcosa che giustifica un'operazione? Perché? Quale sarebbe il piano di uscita o rientro e quando smette di essere valido?».

L'utente non deve inventare prezzi futuri per ottenere il risultato. Prezzo di riferimento, target e orizzonte derivano dal mercato e dal modello al momento del segnale. Il calcolo dei costi resta un controllo interno di convenienza dello scenario, non il prodotto principale.

La prima proposta, conservata nella storia Git al commit `4fcb40b64c86fa36ca087f31dfc04839ffcdf4d0`, è superata. La presente revisione corregge il documento; non dimostra ancora capacità predittiva e non autorizza ordini o deployment.

## 2. Esperienza attesa

Il flusso principale è:

```text
Dati aggiornati -> anomalia -> spiegazione -> VENDERE / ACQUISTARE / ATTENDERE
              -> target opposto + finestra temporale + invalidazione
              -> monitoraggio del piano -> esito verificabile
```

Un'unica scheda mostra strumento ed exchange, momento del rilevamento, prezzo di riferimento, fenomeno osservato, motivazione del segnale, evidenze contrarie, azione proposta, zona target, scadenza e stato della validazione. Non servono inizialmente saldo, quantità possedute o chiavi di trading.

La scheda deve poter suggerire esplicitamente una vendita spot seguita da riacquisto oppure un acquisto spot seguito da vendita. «Attendere» è un risultato motivato, non l'unica azione prevista dal prodotto. In fase sperimentale le stesse schede sono chiaramente etichettate come proposte da valutare in paper trading, senza confonderle con raccomandazioni validate.

## 3. Dati e rilevamento tempestivo

Separare sempre asset, valuta di quotazione, exchange e tipo di mercato. BTC/EUR, BTC/USD e BTC/USDT non sono intercambiabili. Per il prototipo è riutilizzabile il provider pubblico Binance BTC/USDT già presente, con etichetta esplicita; questo non presume l'exchange usato per operare. Prima dell'impiego operativo occorre allineare feed, coppia e costi alla sede effettiva di esecuzione.

Proposta iniziale: acquisizione ogni 60 secondi, osservazioni su barre chiuse a 5 minuti e caratteristiche su finestre 1h, 4h e 24h, con contesto giornaliero. Il polling non garantisce latenza massima. Le barre ancora aperte possono alimentare un preavviso, ma non diventano evidenza storica definitiva. Intervallo delle candele e durata visualizzata nel grafico devono essere indipendenti.

Ogni record porta timestamp del mercato, ricezione, fonte, coppia e stato di completezza. Verificare ordine temporale, duplicati, buchi, valori impossibili e discontinuità del provider prima di classificare un'anomalia di mercato. Un controllo indipendente, quando disponibile sulla stessa coppia o con conversione esplicita, distingue un movimento diffuso da un prezzo isolato; non sostituire silenziosamente la serie primaria.

Quotazioni vecchie oltre 60 secondi, barre mancanti, disallineamenti non risolti o assenza del warm-up richiesto bloccano nuovi suggerimenti operativi e producono «dati insufficienti/non aggiornati». Conservare l'ultimo dato per consultazione non significa poterlo usare per una nuova azione.

Per scaricare lo storico servono paginazione e rispetto dei limiti del provider. La documentazione Binance Spot indica al massimo 1.000 klines per richiesta; richieste oltre tale limite non sono una soluzione per ottenere sei mesi di dati.

## 4. Modello proposto: interpretabile e verificabile

L'approccio raccomandato è un modello quantitativo piccolo e spiegabile, accompagnato da contesto documentato. Un semplice alert percentuale non soddisfa il requisito del piano operativo; un modello linguistico lasciato libero di scegliere prezzi e probabilità non offre calcoli riproducibili. Eventuali modelli più complessi devono dimostrare un miglioramento rispetto alla baseline, non precederla per ragioni estetiche.

Le caratteristiche iniziali candidate sono rendimento rispetto alla volatilità recente, rarità empirica del movimento, volume rispetto al proprio storico, distanza da riferimenti di prezzo e persistenza del trend. Usare pochi input, evitando di contare RSI, medie e altri indicatori correlati come prove indipendenti.

Tenere distinti tre risultati: anomalia statistica, contesto/regime e convenienza dell'operazione. Un movimento raro non prova un errore di prezzo e non implica un'inversione. Una continuazione del trend deve poter prevalere sull'ipotesi di rientro verso la media e portare ad attendere, anche davanti a un forte rialzo o ribasso.

Soglie, finestre, caratteristiche e regole di conferma vanno dichiarate e versionate prima della valutazione finale. Non trasformare un percentile di rarità o un punteggio di anomalia in una probabilità di profitto. Non scegliere retroattivamente il modello che rende convincente l'evento appena osservato.

## 5. Spiegare il perché senza inventare cause

La spiegazione contiene due livelli separati:

- **Perché il sistema considera il movimento anomalo o interessante:** valori misurati, confronti storici, contesto del trend e condizioni che hanno attivato o bloccato il segnale.
- **Quali eventi potrebbero aver contribuito al movimento:** notizie ed eventi pertinenti con fonte, momento dell'evento, pubblicazione e momento in cui erano disponibili al sistema.

Una notizia coincidente non dimostra causalità. Usare formulazioni come «evento concomitante» o «possibile contributo» quando questo è il livello dell'evidenza. Se non esiste una causa verificabile, scrivere «causa non confermata» senza inventare liquidazioni, flussi istituzionali o altri dati non acquisiti.

Mostrare anche le evidenze contrarie all'operazione. L'assenza di notizie non dimostra che il movimento sia ingiustificato. Se un input contestuale è necessario per una regola e manca, quella regola si astiene.

La prima spiegazione deve funzionare con testo strutturato e fonti. Un assistente AI è facoltativo per sintetizzare evidenze già disponibili: non genera autonomamente target, probabilità, dati o nessi causali. Una sua indisponibilità non interrompe il nucleo quantitativo.

## 6. Target e orizzonte generati dal segnale

Alla nascita del segnale congelare uno snapshot con prezzo osservato, intervallo d'ingresso ammissibile, target per l'operazione opposta, livello/condizione d'invalidazione, durata massima e ipotesi di costo. I prezzi sono nella valuta e sull'exchange esplicitati.

La proposta metodologica è stimare scenari successivi a eventi storici comparabili, condizionati almeno a direzione, intensità e regime, usando solo informazioni disponibili prima dell'evento valutato. Volatilità, livelli osservati e distribuzioni degli esiti aiutano a costruire zone target; non sono garanzie che tali zone verranno raggiunte.

Gli orizzonti candidati iniziali sono 24, 48 e 72 ore, come proposta coerente con operazioni su più giornate, non come promessa temporale. La selezione dell'orizzonte e dei target fa parte del modello validato e deve essere congelata prima del test finale. Non usare per ogni evento l'orizzonte che funziona meglio guardando il futuro.

L'evento da stimare è «raggiungere il target prima dell'invalidazione ed entro l'orizzonte», non soltanto «chiudere più in alto/più in basso». Conteggiare anche mancati raggiungimenti e movimenti iniziali avversi. L'intervallo dei tempi calcolato solo sui successi va identificato come tale.

Mostrare probabilità numeriche solo se accompagnate da numerosità effettiva, periodo, metodo, incertezza e verifica di calibrazione fuori campione. In assenza di supporto sufficiente usare «probabilità non stimabile»; si può mostrare una zona tecnica sperimentale con la sua origine, senza attribuirle una confidenza fittizia. Nessun target credibile o margine insufficiente dopo i costi deve produrre «attendere».

La gestione del rischio, inclusa l'invalidazione, è parte del piano. Il sistema non sceglie autonomamente quale quota del patrimonio impiegare e non presenta i risultati come rendimento fiscale netto.

## 7. Ciclo operativo e significato della scadenza

Supportare separatamente:

- **SELL -> BUY:** vendita di BTC disponibili, poi possibile riacquisto. Se il prezzo continua a salire, rientrare più in alto può ridurre i BTC recuperabili; il fallimento del piano non viene nascosto aspettando indefinitamente.
- **BUY -> SELL:** acquisto con liquidità disponibile, poi possibile vendita. Non consentire posizioni negative, prestiti o leva.

L'azione suggerita non equivale a un'operazione eseguita. La UI distingue «solo osservato», «seguito in simulazione» ed eventuale conferma manuale di esecuzione. La disponibilità di BTC o liquidità, se non dichiarata, resta sconosciuta; il suggerimento esplicita la condizione senza presumere saldi.

Il target si monitora **entro** la finestra, non soltanto dopo aver aspettato un numero fisso di giorni. Se viene raggiunto prima, avvisare subito; se arriva prima l'invalidazione o la scadenza, avvisare che il piano è invalidato o scaduto. La scadenza richiede una nuova valutazione, non un obbligo automatico di eseguire l'operazione opposta.

Un segnale ha inoltre una propria validità d'ingresso, distinta dalla durata del piano. I valori di questa policy appartengono alla configurazione versionata del modello. Fuori dalla fascia d'ingresso o dopo la scadenza non presentare un vecchio segnale come attuale.

Non spostare retroattivamente target, ingresso o durata per far risultare vincente un piano. Una revisione è un nuovo record collegato, con motivo e timestamp. Deduplicare alert per evento/stato e impedire piani concorrenti incompatibili sulla stessa porzione simulata.

## 8. Backtest e verifica degli esiti sono nel primo incremento

La valutazione è un requisito del nucleo, non una fase opzionale rimandata dopo grafici e calcolatore. Separare sviluppo, validazione cronologica e un periodo finale intatto; usare analisi walk-forward con separazione delle finestre sovrapposte all'orizzonte del segnale. Registrare anche le configurazioni scartate per non nascondere la selezione multipla.

I backtest non possono usare candele future, notizie pubblicate dopo il segnale, livelli ricostruiti con dati successivi o prezzi di esecuzione non disponibili. Se manca uno storico contestuale affidabile, testare separatamente il nucleo quantitativo e verificare il livello news in paper trading; non attribuire al sistema completo il risultato del solo nucleo.

Includere commissioni di entrambe le operazioni, spread e slippage con convenzioni esplicite, nessun doppio conteggio e analisi di sensibilità. Se target e invalidazione sono toccati nella stessa candela e l'ordine non è ricostruibile, usare dati più fini oppure un esito conservativo/indeterminato dichiarato. Nessun riempimento garantito al target; gestire gap e limiti di esecuzione.

Misurare target raggiunto prima dell'invalidazione, scadenze, perdite, peggior movimento avverso, drawdown, numerosità effettiva e risultati per regime. Confrontare SELL -> BUY con mantenere gli stessi BTC e BUY -> SELL anche con rimanere liquidi, usando le stesse risorse iniziali. Mostrare sia patrimonio nella valuta quotata sia quantità BTC, compresa la valorizzazione dei piani ancora aperti: non selezionare soltanto operazioni chiuse in profitto.

Il primo rilascio di ricerca genera proposte sperimentali, spiegazioni e piani monitorati senza denaro reale. La promozione a uso operativo richiede un rapporto fuori campione e una verifica prospettica, con criteri registrati prima della prova. Un rapporto può concludere che non c'è un vantaggio dimostrato: in quel caso mantenere lo strumento in ricerca, senza trasformare il risultato negativo in una promessa commerciale.

## 9. Architettura e perimetro del primo incremento

Riutilizzare l'applicazione esistente senza riscrivere il terminale:

1. adapter dati e archivio locale di mercato con qualità/provenienza;
2. motore puro di caratteristiche, segnali e piani, condiviso da replay storico e monitoraggio;
3. servizio di spiegazione con evidenze e fonti;
4. archivio append-only degli eventi e degli esiti, separato dai dati personali del portafoglio;
5. widget BTC con scheda operativa, stato del piano e storico; alert persistenti nell'app.

Il monitoraggio deve vivere nel processo backend e continuare senza la pagina aperta finché quel processo è attivo. Se PC/processo si spegne, il monitoraggio si interrompe: mostrarlo chiaramente. Recuperare lo storico al riavvio senza fingere che un alert scaduto sia stato consegnato in tempo.

Notifiche esterne a telefono/browser richiedono un canale configurato e un servizio attivo: non sono automaticamente garantite dal fork o da questa specifica. Il canale esterno va verificato end-to-end prima di dichiarare alert affidabili a pagina chiusa; nessuna automazione ChatGPT è stata creata con questo documento.

La prima implementazione deve percorrere l'intero flusso dati -> anomalia -> spiegazione -> proposta e piano sperimentale -> esito. Non sostituirlo nuovamente con una UI di prezzi manuali. Eventuali sotto-incrementi tecnici devono contribuire a quel flusso.

## 10. Privacy, limiti e test

Usare dati di mercato pubblici per rilevazione e backtest. Non committare saldi, operazioni personali, log privati, credenziali o archivi runtime. I dettagli di eventuali operazioni reali richiedono un opt-in separato alla persistenza; la ricerca funziona con contabilità sintetica. Nessun accesso autenticato all'exchange, nessun ordine automatico e nessun deployment pubblico in questa revisione.

Testare: determinismo del replay; esclusione dei dati futuri; qualità e freschezza del feed; separazione USD/USDT/EUR; astensione per dati insufficienti; differenza tra anomalia e probabilità; costi e contabilità spot; target/invalidation/timeout nell'ordine corretto; mancata esecuzione; deduplicazione; ripartenza; spiegazioni senza fonti; benchmark e casi in perdita. Aggiungere verifica browser desktop/mobile e controlli di privacy/rete pertinenti.

I test automatici del codice e le build non certificano profittabilità. Il rapporto statistico e i test ingegneristici sono artefatti distinti. Prima di un merge applicativo servono test e CI pertinenti verificati; la CI esistente si attiva su push a main e su pull request, non su ogni push documentale a questo branch.

## 11. Fonti e stato della revisione

Fonti consultate il 13 ottobre 2026, come motivazione metodologica e documentazione, non come validazione di una strategia attuale:

- Binance Spot, Market Data: https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market
- Fidelity, RSI: https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/RSI — in trend forti le condizioni estreme possono persistere.
- Liu e Tsyvinski, Risks and Returns of Cryptocurrency, NBER WP 24877 (2018; versione pubblicata 2021): https://www.nber.org/papers/w24877 — evidenza storica di momentum, non garanzia sui mercati correnti.
- Novy-Marx, Backtesting Strategies Based on Multiple Signals, NBER WP 21329 (2015): https://www.nber.org/papers/w21329 — rischio di overfitting nella combinazione/selezione dei segnali.

Questa revisione modifica soltanto la specifica sul branch documentale e sostituisce il precedente obiettivo. Nessun motore, feed, backtest, alert o modello predittivo è stato implementato o verificato in questo checkpoint. L'architettura e le proposte metodologiche richiedono revisione prima del piano esecutivo; la direzione del prodotto recepisce la correzione esplicita ricevuta.
