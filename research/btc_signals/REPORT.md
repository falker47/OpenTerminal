# BTC spot — primo risultato della ricerca sui segnali

**Data: 13 ottobre 2026. Stato: esperimenti E1/E2 eseguiti; nessun candidato validato per uso operativo.**

## Risultato principale

Le regole testate non hanno prodotto un segnale robusto da inserire nell'applicazione come raccomandazione. I due candidati selezionati sul 2023–2024 perdono nel test separato del 2025, pur chiudendo circa il 62% dei cicli in positivo. Una baseline di acquisto dopo ribassi più marcati è positiva nel 2025, ma l'intervallo di incertezza include ancora una media negativa: resta un riferimento di ricerca, non la «formula vincente».

Questo risultato riguarda le famiglie, i costi e le convenzioni qui specificati. Non dimostra l'inefficacia di ogni possibile strategia BTC e non esaurisce la ricerca.

## Dati effettivamente utilizzati

Fonte: archivio ufficiale Binance Spot, BTCUSDT, candele orarie. Scaricati e verificati 73 ZIP mensili, da dicembre 2019 a dicembre 2025. Dicembre 2019 serve da warm-up. Ogni ZIP è confrontato con il checksum SHA-256 pubblicato; il pacchetto Actions e il CSV consolidato sono stati verificati nuovamente nel container.

Il CSV contiene **53.313 candele**. Otto record con timestamp di chiusura irregolari sono conservati nel registro di quarantena ma non usati. Ci sono 39 ore mancanti nel reticolo consolidato, comprendenti le otto escluse, distribuite in 16 discontinuità. Nessuna interpolazione. Per le caratteristiche del segnale è richiesta una finestra completa di 745 candele: un'interruzione causa quindi un periodo di astensione, non una sostituzione del dato. Il 2025 contiene tutte le 8.760 ore attese.

Acquisizione verificata dalla run GitHub Actions `38363774036`, commit `330fdc24c93dcaf6dfc26e677381da1afa316231`. I primi due tentativi di acquisizione erano falliti sul controllo dei timestamp; la correzione mantiene quarantena e tracciabilità anziché disattivare il controllo.

CSV SHA-256: `de110de0333525d14b46c287fc7fe20a1353ea2e40fcb5710c7c78ac13e590da`.

## Esperimenti e criteri congelati

E1 confronta sei famiglie: sola escursione normalizzata per volatilità; aggiunta del rallentamento; rallentamento con volume; con attenuazione dei flussi taker; con filtro dell'andamento precedente; con flussi e andamento precedente insieme. Target di 0,5 oppure 1 sigma giornaliera, invalidazione a 1 sigma, durata massima 24/48/72 ore, due direzioni spot. Sono 72 configurazioni.

La soglia E1 di 2,5 produce troppo pochi episodi: nessuna configurazione raggiunge 50 trade determinati nello sviluppo 2020–2022. Non sono stati abbassati i minimi a posteriori. E1 è preservato come risultato negativo di screening.

E2 modifica soltanto la soglia: 1,5 e 2,0. Altre 144 configurazioni, registrate prima di calcolarne gli esiti. Totale: **216 configurazioni**, non 216 strategie indipendenti. Sviluppo 2020–2022; selezione 2023–2024; test 2025 separato. Nel 2025 sono valutati soltanto baseline e selezionato per direzione, quattro confronti complessivi. Non è stato scelto il migliore tra tutti i modelli sul 2025.

La selezione massimizza la media logaritmica netta nella validazione tra modelli con almeno 50 trade determinati nello sviluppo e 30 nella validazione. Un «selezionato» può essere soltanto il meno negativo: il nome non implica approvazione operativa. Devono comunque passare sviluppo positivo, entrambi gli anni di validazione positivi, almeno 30 trade nel holdout, limite inferiore bootstrap positivo, stress dei costi positivo e nessun esito indeterminato nel holdout.

Il protocollo E1 è stato salvato nel commit `8bdaa4e52c33864e8b7de629b8a52de5aed98239`; l'espansione E2 nel commit `cfdee552d5b1aad2b8b8a8a8f118976e94d42af8`; la selezione E2 nel commit `067b9b17f4d187651f25bb1b7cbda1b74375b939`, prima del calcolo degli esiti 2025.

## Convenzioni economiche

Costo base per ogni lato: commissione 0,10% e slippage 0,05%, circa 0,30% sul ciclo completo. Sono assunzioni di ricerca, non le commissioni dichiarate dell'utente. Spread e slippage sono aggregati nell'attrito assunto, non sottratti nuovamente. Le imposte non sono incluse.

SELL→BUY misura la variazione di BTC rispetto a conservare gli stessi BTC. BUY→SELL misura la variazione di USDT rispetto a rimanere liquidi. Non si trattano vendite spot come posizioni short. Commissioni modellate sull'asset ricevuto: fattore comune `(1-fee)^2 * (1-slip)/(1+slip)`, moltiplicato per prezzo ingresso/prezzo uscita per SELL→BUY, o per il rapporto opposto per BUY→SELL.

Ingresso ipotizzato all'apertura dell'ora successiva a un segnale chiuso. Target e invalidazione derivano dalla volatilità disponibile allora. Stop prima del target quando entrambi sono toccati nella stessa candela e l'ordine è sconosciuto; gap avverso valorizzato all'apertura; gap favorevole non riceve più del target. Alla scadenza il backtest chiude il ciclo: convenzione sperimentale, non regola definitiva per l'app. Non si aspetta indefinitamente un rientro favorevole.

## Risultati del test 2025

| Regola congelata | Cicli | Cicli positivi | Media netta per ciclo | Composizione dei cicli |
|---|---:|---:|---:|---:|
| SELL→BUY baseline: shock 2,0, target 1 sigma, 48h | 24 | 54,17% | −0,0618% BTC | −1,98% BTC |
| SELL→BUY selezionato: shock 1,5 + rallentamento/flussi, target 0,5 sigma, 48h | 29 | 62,07% | −0,4054% BTC | −11,46% BTC |
| BUY→SELL baseline: shock 2,0, target 1 sigma, 48h | 34 | 67,65% | +0,4543% USDT | +15,89% USDT |
| BUY→SELL selezionato: shock 1,5, target 0,5 sigma, 72h | 42 | 61,90% | −0,4222% USDT | −16,72% USDT |

La composizione assume l'impiego sequenziale dell'intera porzione simulata e l'esecuzione di tutti i cicli, senza sovrapposizioni; non è un rendimento conseguibile garantito né un'indicazione di quanto capitale impiegare. Le unità delle due direzioni sono differenti e non vanno sommate. Non ci sono cicli indeterminati nel 2025; il BUY→SELL selezionato ha un caso di doppia barriera, trattato come invalidazione.

Nel SELL→BUY selezionato: 17 target, 10 invalidazioni, 2 scadenze. Nel BUY→SELL selezionato: 26 target e 16 invalidazioni. La combinazione di guadagni piccoli e perdite maggiori spiega perché circa il 62% di successi non basti. Entrambi sono negativi persino senza costi nel 2025: rispettivamente −0,1061% e −0,1229% medi per ciclo.

I candidati erano già fragili prima del holdout. SELL→BUY: media sviluppo −0,3225%, validazione −0,0750%; un esito indeterminato nel 2023 è contato e non trasformato in zero. BUY→SELL: sviluppo −0,2272%; validazione aggregata +0,1869%, ma 2023 +0,4775% e 2024 −0,0706%. Il risultato aggregato nascondeva instabilità fra periodi.

## Baseline positiva e incertezza

La baseline BUY→SELL resta positiva nello scenario di stress (commissione 0,20% e slippage 0,10% per lato): +0,1531% medio per ciclo nel 2025. Questo la distingue dai candidati selezionati, ma non certifica un vantaggio persistente.

Bootstrap a blocchi mensili, 20.000 ricampionamenti, dodici mesi inclusi anche senza trade; intervalli al 98,75% per i quattro confronti finali. Per la baseline BUY→SELL, l'intervallo della media geometrica netta per ciclo è circa **[−0,13%; +1,01%]**. Include zero. Un solo anno e dodici blocchi forniscono potenza limitata; la correzione non elimina ogni forma di selezione multipla o instabilità temporale. Nessun candidato supera i gate preregistrati.

Controllo buy-and-hold separato: su questa stessa coppia e questo stesso 2025, prezzo iniziale 93.576 USDT e finale 87.648,22 USDT, variazione −6,3347%; con acquisto e liquidazione finale ai costi base, −6,6154%. Per SELL→BUY il benchmark naturale resta mantenere 1 BTC: il selezionato termina con circa 0,88545 BTC per BTC iniziale. Un benchmark annuale positivo o negativo non sostituisce la verifica dell'aspettativa del segnale.

## Verifiche e limiti

35 test automatici locali passati: parsing, checksum, quarantena, costi, target/stop/timeout, ordinamento conservativo, gap, indipendenza delle caratteristiche da dati futuri, warm-up, ingresso successivo, cooldown e selezione distinta per direzione. Tutti i quattro gruppi di trade 2025 sono stati anche ricontrollati con aritmetica indipendente dei saldi BTC/USDT. I test dell'applicazione e le build server/web sono già passati sulla correzione dell'acquisizione; la CI dedicata alla ricerca ripete l'esperimento e confronta `expected_e2.json` sul commit di pubblicazione. Il suo esito va verificato nella run associata. La CI verde verifica il codice, non la profittabilità.

Questa fase non comprende news, spiegazioni causali, order book, esecuzione live, ritardo umano, fiscalità, dimensionamento delle posizioni o una validazione prospettica. L'equity intratrade e il drawdown continuo non sono stati ancora validati: la composizione dei cicli non è un rapporto completo di rischio. I piani su dati mancanti sono esclusi con conteggio esplicito; tale esclusione può influire sulla rappresentatività del campione. Non c'è un'interfaccia di segnali pronta all'uso.

Il 2025 è ormai osservato. Non riutilizzarlo come test «vergine» per nuove ottimizzazioni. La prossima ipotesi da studiare è una selezione stabile per regime con confronti espliciti fra rientro e continuazione, anziché aggiungere indicatori e massimizzare una sola media biennale. Usare sviluppo e validazioni cronologiche a finestra mobile; riservare dati non ancora analizzati per il prossimo test finale.

Fonti primarie: archivio/dettagli Binance https://github.com/binance/binance-public-data ; per numeri, ranking e singoli trade, manifest e output JSON/CSV del pacchetto riproducibile E1/E2. Nessuna quotazione corrente o operazione personale è inclusa.
