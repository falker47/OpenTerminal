# BTC Spot — specifica del primo incremento

Stato: **PROPOSTA DA REVISIONARE, NON IMPLEMENTATA**.
Data: 13 ottobre 2026.
Repository: `falker47/OpenTerminal`.
Baseline letta: `aed097c680cd8ec1c391ae06966babe7d6d91fc6`.
Upstream: `ErTasselli/OpenTerminal`; licenza e attribuzioni restano inalterate.

## 1. Risultato atteso

Un simulatore manuale di vendita e successivo riacquisto di BTC già posseduti. Deve rispondere a: «A quale prezzo potrei riacquistare almeno la stessa quantità di BTC, considerando i costi dichiarati?». Non suggerisce quando operare, non stima la probabilità di un ribasso e non esegue ordini.

L'obiettivo della prima iterazione è un calcolo verificabile e indipendente dai provider di mercato, non il completamento dell'intera dashboard finanziaria.

## 2. Scelta architetturale proposta

Aggiungere un widget isolato all'applicazione esistente, con un modulo di calcolo puro e test dedicati. Riutilizzare il contenitore dei widget, senza riscrivere il prodotto né modificare il registro delle operazioni.

Alternative considerate: una nuova applicazione separata eviterebbe parte del codice ereditato ma duplicherebbe interfaccia e manutenzione; integrare subito il simulatore nel portafoglio lo accoppierebbe alla persistenza e a un modello contabile che oggi non registra commissioni. Il widget isolato mantiene piccolo e reversibile il primo intervento.

I calcoli devono avvenire nel browser senza inviare gli input al server, all'assistente AI, a log o a servizi esterni. Il simulatore non introduce nuove richieste di rete. Gli altri widget mantengono il loro comportamento: questa specifica non rende offline l'intera applicazione.

## 3. Input e convenzioni

- Quantità di BTC da vendere: positiva, al massimo otto decimali; rappresenta solo la porzione simulata, non richiede il saldo totale.
- Valuta di quotazione: scelta esplicita fra EUR, USD e USDT. Nessuna conversione automatica e nessuna equivalenza implicita fra USD e USDT.
- Prezzo di vendita e prezzo ipotizzato di riacquisto: positivi, nella medesima valuta per BTC. Sono prezzi attesi di esecuzione, non quotazioni live.
- Commissione percentuale di vendita e di acquisto: separate, esplicitamente indicate. Zero è ammesso ma deve restare visibile come assunzione.
- Costi fissi di vendita e acquisto: non negativi, nella valuta di quotazione.
- Accantonamento facoltativo: importo non negativo nella valuta di quotazione, da non reinvestire nella simulazione. È un vincolo di liquidità, non un calcolo delle imposte.

Convenzione delle commissioni: quella di vendita viene dedotta dai ricavi; quella di acquisto è pagata nella valuta di quotazione in aggiunta al controvalore acquistato. Pagamenti delle commissioni in BTC o in token di terzi sono fuori scope: l'interfaccia deve avvertire che richiedono un modello diverso.

Spread e slippage sono incorporati nei prezzi attesi di esecuzione inseriti dall'utente. Non sottrarli una seconda volta come costi separati. La prima versione non tenta di stimarli automaticamente.

## 4. Modello matematico

Siano:

- `q`: BTC venduti;
- `Ps`: prezzo atteso di vendita;
- `Pb`: prezzo atteso di riacquisto;
- `fs`, `fb`: commissioni frazionarie di vendita e acquisto, ciascuna in `[0, 1)`;
- `Ks`, `Kb`: costi fissi di vendita e acquisto;
- `R`: accantonamento facoltativo, distinto da costi e imposte effettive.

```text
Ricavi_lordi = q * Ps
Commissione_vendita = Ricavi_lordi * fs
Ricavi_netti_vendita = Ricavi_lordi - Commissione_vendita - Ks
Budget_acquisto = Ricavi_netti_vendita - R - Kb
BTC_teorici_riacquistabili = Budget_acquisto / (Pb * (1 + fb))
Prezzo_pareggio_BTC = Budget_acquisto / (q * (1 + fb))
```

Un budget negativo o nullo blocca i risultati di riacquisto e mostra «Budget insufficiente con questi costi/accantonamenti». Non mostrare quantità negative, prezzi nulli utilizzabili o un segnale operativo.

Usare aritmetica decimale verificabile. La quantità mostrata come riacquistabile è arrotondata per difetto a otto decimali, con indicazione della liquidità residua. Non usare un arrotondamento per eccesso che suggerisca più BTC di quelli finanziabili. Il prezzo di pareggio è una soglia teorica: tick size, quantità minima e limiti dell'exchange non sono modellati.

Gli importi originali e gli intermedi mantengono la precisione di calcolo; formattazione e arrotondamento di visualizzazione non devono alimentare nuovi calcoli.

## 5. Output e confronto con mantenere BTC

Mostrare ricavi lordi, commissioni, costi fissi, accantonamento e budget residuo separatamente. Poi mostrare:

1. prezzo teorico di pareggio per recuperare la quantità venduta;
2. ribasso percentuale necessario rispetto al prezzo atteso di vendita;
3. BTC riacquistabili al prezzo ipotizzato, differenza assoluta e percentuale rispetto a `q`;
4. eventuale liquidità residua dovuta all'arrotondamento.

Il benchmark è conservare gli stessi `q` BTC, nello stesso intervallo ipotetico, senza operare. Eventuali BTC non venduti restano identici nei due scenari e non servono come input.

La differenza di BTC non è un rendimento storico, una plusvalenza fiscale o un confronto completo di patrimonio dopo le imposte. Se esiste un accantonamento, mostrarlo separatamente: riduce il budget reinvestibile ma non è automaticamente denaro perso o imposta pagata. Evitare di presentare il risultato come «profitto netto fiscale».

## 6. Esempi sintetici per l'accettazione

I seguenti importi sono inventati per verificare le formule; non sono quotazioni di mercato né dati di un portafoglio.

Con `q = 0,01 BTC`, `Ps = 100.000`, commissioni `fs = fb = 0,1%`, nessun costo fisso e nessun accantonamento:

- ricavi netti della vendita: `999` unità della valuta scelta;
- prezzo teorico di pareggio: circa `99.800,1998002` per BTC;
- con `Pb = 95.000`, quantità teorica: circa `0,01050528418949 BTC`, quantità conservativa: `0,01050528 BTC`;
- con `Pb = 100.000` o `110.000`, i BTC riacquistabili sono inferiori a `0,01`;
- senza alcun costo, riacquistando allo stesso prezzo si recupera esattamente `q`.

Sono stati controllati separatamente con aritmetica decimale l'esempio, l'identità al pareggio e il peggioramento a prezzo invariato/in rialzo. Questi controlli matematici della specifica non sono test dell'applicazione.

## 7. UX e riservatezza

Widget leggibile anche su schermo stretto, con etichette italiane esplicite e un riepilogo compatto; errori associati ai rispettivi campi. Gestire correttamente l'inserimento decimale, evitando che stringhe vuote o parziali diventino zero in modo silenzioso.

Il form iniziale non contiene saldi o prezzi reali. Un esempio dimostrativo, se presente, deve richiedere una scelta esplicita e restare etichettato come sintetico. In questa prima versione nessuna persistenza degli input, nessun import di transazioni e nessuna API key. Non aggiungere gli input allo stato persistito del layout, agli URL o a messaggi dell'assistente AI.

La dicitura permanente è: «Simulazione su ipotesi inserite. Non prevede il mercato, non calcola le imposte e non esegue ordini». Non utilizzare «compra», «vendi», semafori di convenienza o percentuali di probabilità come raccomandazione.

## 8. Test e criteri di completamento dell'implementazione

Prima della UI, scrivere test del modulo di calcolo per: assenza di costi, commissioni asimmetriche, costi fissi, accantonamento, soglia di pareggio, riacquisto più caro, quantità frazionarie, arrotondamento e liquidità residua. Testare separatamente input vuoti, negativi, non finiti, percentuali fuori intervallo e budget insufficiente.

Verificare le proprietà: a parità di altri input un costo maggiore non aumenta i BTC riacquistabili; un prezzo di riacquisto maggiore non aumenta la quantità; in assenza di costi fissi/accantonamento la soglia teorica di pareggio non dipende da `q`.

Aggiungere una prova d'integrazione del widget e un comando di test frontend eseguito dalla CI, non soltanto test eseguibili a mano. La CI attuale legge i test server e le build server/web: la sola build frontend non verifica il calcolo nuovo.

Eseguire test server preesistenti, test nuovi, build server/web e una verifica browser desktop/mobile. Verificare nel browser che modificare il simulatore non invii gli input in rete e che il riavvio non li ripristini. Pubblicare una PR applicativa solo dopo verifiche locali disponibili; nessun merge o rilascio con controlli richiesti falliti o mancanti senza una decisione esplicita.

## 9. Confini e fasi successive

Esclusi dal primo incremento: ordini automatici, exchange autenticati, short, leva, derivati, segnali predittivi, AI decisionale, motore fiscale, backtesting, deploy pubblico e modifiche dei dati SQLite esistenti.

Resta la direzione generale discussa per il fork: dashboard BTC dedicata, diario con costi e confronto storico con buy-and-hold. Questi sono incrementi successivi, non funzionalità dichiarate come già costruite. Alert e backtesting restano ulteriori estensioni, da valutare dopo qualità dei dati e contabilità.

## 10. Stato del checkpoint

Fork e accesso in scrittura verificati; `main` di partenza identificato. Questa modifica aggiunge soltanto la specifica su un branch separato. Nessun codice applicativo, dipendenza, workflow, dato di portafoglio o licenza modificati. Nessun deploy e nessuna connessione a exchange.

La specifica richiede revisione prima di diventare il contratto dell'implementazione. Il prossimo artefatto, dopo la revisione, è il piano operativo del primo incremento con i file effettivi e le verifiche eseguibili. L'assenza di una run CI sul fork non equivale a CI verde.
