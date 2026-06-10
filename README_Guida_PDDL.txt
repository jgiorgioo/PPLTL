===============================================================================
        STAGE PIANIFICAZIONE AUTOMATICA (PDDL) - DIARIO DI BORDO & SETUP
===============================================================================

Questo archivio contiene i modelli PDDL, i file di configurazione e gli script
di orchestrazione per la generazione massiva del benchmark dello stage (fino a 
50.000 istanze). Il progetto è configurato per girare in un ambiente ibrido 
Windows (VS Code) + Linux (WSL Ubuntu) per garantire la massima stabilità e 
velocità di calcolo.

-------------------------------------------------------------------------------
1. ARCHITETTURA DELL'AMBIENTE DI LAVORO E PIPELINE AUTOMATICA
-------------------------------------------------------------------------------
Il progetto è centralizzato e orchestrato da uno script Python principale 
(main.py) che gestisce in modo polimorfico i diversi domini delegando l'infrastruttura
a un manager interno (generators_manager.py):

* Generazione File (.pddl, .plan): Coordinata tramite fabbriche stateless 
  (generators.py) che invocano i singoli generatori di dominio (Python o binari).
* Verifica di Fattibilità e Validazione Sintattica: Disaccoppiata e distribuita 
  mediante una separazione netta delle responsabilità (Separation of Concerns):
  - Modulo Solver (solver.py): Invoca in modo agnostico e controllato il planner 
    Fast Downward in WSL per verificare se il problema candidato è risolvibile 
    (Fattibilità) restituendo un piano temporaneo (sas_plan).
  - Modulo Validator (validator.py): Prende il piano temporaneo prodotto dal 
    solver e lo convalida formalmente mediante il tool VAL (validate), assicurando 
    la correttezza sintattica assoluta delle transizioni prima della persistenza.
  - Modulo Utility (util.py): Riceve le istanze che hanno superato congiuntamente 
    la verifica di fattibilità e validazione, le rinomina con indici sequenziali 
    e coordina in modo atomico lo spostamento e l'archiviazione finale.
* Ottimizzazione Sokoban (IPC 2023): Il manager applica un bypass strategico; 
  constatato che il generatore produce intrinsecamente un piano perfetto invertito, 
  il sistema intercetta direttamente il file .plan nativo sul disco e lo archivia 
  tramite le utility, azzerando i tempi di calcolo.

I percorsi di output sono rigidamente standardizzati dai parametri del ciclo:
* Problemi PDDL: Salvati nella cartella di dominio (es. plans/uncostrained/sokoban/) 
  e rinominati progressivamente (es. sokoban-1.pddl, sokoban-2.pddl) tramite la 
  funzione esterna rename_problem in util.py.
* Piani Soluzione: Spostati nella sottocartella delle soluzioni dedicata 
  (es. plans/uncostrained/sokoban/solutions/) adottando la nomenclatura 
  standardizzata [nome_dominio]-[ID_progressivo].plan.

-------------------------------------------------------------------------------
2. COMPILAZIONE E BUILD DI PLANNER, VALIDATORI E GENERATORI NATIVI (WSL)
-------------------------------------------------------------------------------
Per garantire le massime prestazioni di calcolo ed evitare i colli di bottiglia
di I/O legati ai sistemi di sincronizzazione cloud di Windows (es. OneDrive), 
tutti i motori core sono compilati ed eseguiti nativamente nell'ambiente Linux:

A. Compilazione di Fast Downward (Planner Core):
   1. Scaricato il codice sorgente nella home di Linux WSL:
      cd ~ && git clone https://github.com/aibasel/downward && cd downward
   2. Compilato in modalità Release ottimizzata per la velocità di CPU:
      python3 build.py release

B. Compilazione di VAL (The PDDL Plan Validator):
   1. Installare i pacchetti Debian core necessari alla build e alla rigenerazione 
      del codice del parser (inclusi i generatori sintattici flex e bison richiesti 
      esplicitamente dalle specifiche di sistema):
      sudo apt update && sudo apt install -y build-essential cmake g++ flex bison git
   2. Configurare l'ambiente di compilazione isolato all'interno della directory 
      del repository ed eseguire la generazione dei file di configurazione CMake, 
      forzando la modalità Release e iniettando i vincoli di compatibilità minimi 
      per le versioni recenti del software di build:
      cd ~/VAL && mkdir -p build && cd build
      cmake -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_BUILD_TYPE=Release ..
   3. Avviare il processo di compilazione parallela nativa sfruttando la totalità 
      dei core hardware rilevati sul processore della macchina ospite Linux:
      cmake --build . --config Release -- -j2
      
C. Compilazione del Generatore Goldminer:
   1. Spostarsi nella cartella dei sorgenti C++ del generatore:
      cd [percorso_progetto]/pddl-generators/goldminer
   2. Compilare il file eseguibile binario tramite il Makefile nativo:
      make
   3. Verificare l'eseguibile generato (gold-miner-generator).

-------------------------------------------------------------------------------
3. COESISTENZA E COLLABORAZIONE CROSS-PLATFORM (WINDOWS / WSL)
-------------------------------------------------------------------------------
Una delle domande centrali di questa architettura è: come fa lo script a girare 
su Windows se il planner Fast Downward e il validatore VAL non sono nativi per 
Windows e richiedono Linux?

Il sistema sfrutta l'interoperabilità profonda offerta da WSL (Windows Subsystem 
for Linux) e la natura "bridge" di Python:

* Esecuzione interamente interna a Linux: Lo script orchestratore principale 
  (main.py) NON viene eseguito dall'ambiente Windows, ma viene lanciato dal 
  terminale Linux WSL (tramite il comando 'python3 main.py'). Essendo l'intero 
  processo Python nativo di Linux, esso ha pieno e diretto accesso sia a Fast 
  Downward sia a VAL (compilati in formato ELF per Linux) sia ai generatori in C++.
* Condivisione Trasparente del File System (9P File System): Sebbene l'esecuzione 
  avvenga nel kernel Linux di WSL, i file vengono salvati all'interno dei dischi 
  locali (es. /mnt/c/Users/...). WSL monta automaticamente le partizioni Windows 
  all'interno dell'albero delle directory Linux.
* Il Vantaggio del Modello Ibrido: Questo approccio consente un disaccoppiamento 
  perfetto. Windows gestisce l'interfaccia grafica (IDE VS Code per la scrittura 
  dei modelli e l'ispezione visiva dei file generati), mentre Linux WSL si fa 
  carico del calcolo pesante non-nativo (pianificazione dei problemi in Fast 
  Downward, compilazione dei binari C++ e validazione formale in VAL), garantendo 
  una portabilità totale senza dover ricorrere a macchine virtuali pesanti.

-------------------------------------------------------------------------------
4. DESCRIZIONE DEL LAVORO SVOLTO (FOCUS INGEGNERISTICO)
-------------------------------------------------------------------------------
Il nucleo del lavoro di stage si è concentrato sull'ingegnerizzazione e sul 
refactoring di una pipeline di benchmarking frammentata, trasformandola in un 
sistema di automazione centralizzato, incapsulato e strutturalmente scalabile.

I principali contributi includono:
* Disaccoppiamento e Astrazione (Polimorfismo): Progettazione di un'interfaccia 
  comune per i generatori (PDDLGenerator). Questo ha permesso di uniformare sotto 
  un unico flusso logico sia tool che scrivono in STDOUT (CityCar, Goldminer) sia 
  tool che interagiscono direttamente con il file system (Sokoban, MiniGrid), 
  nascondendo i dettagli implementativi all'interfaccia utente (main.py).
* Architettura Modulare per Scopi Scientifici: Refactoring radicale delle funzioni 
  di verifica e persistenza. L'estrazione dei moduli funzionali puri 'solver.py' 
  e 'validator.py' ha separato il problema computazionale della ricerca (Fast Downward) 
  dalla verifica formale e deterministica (VAL). Questa struttura garantisce lo 
  standard scientifico internazionale richiesto nei benchmark di IA.
* Ottimizzazione dei Tempi di Calcolo (Bypass Strategico): Riconoscendo che il 
  generatore di Sokoban produce nativamente piani validi e certificati, la pipeline 
  è stata ingegnerizzata per intercettare il file .plan generato dal sottoprocesso 
  e spostarlo istantaneamente in modalità I/O pura. Questo ha ridotto il tempo 
  di computazione per Sokoban a 0 millisecondi di pianificazione per istanza, 
  rendendo fattibile il target di 50.000 problemi.
* Gestione Robusta del Ciclo di Vita (Garbage Collection): Sviluppo di un sistema 
  sincrono di cattura differenziale (calcolo dei nuovi file tramite set-difference). 
  Il manager isola i file associati all'ID provvisorio e pulisce immediatamente 
  qualsiasi residuo (.plan orfani di Sokoban o file intermedi output.sas e sas_plan 
  locali) sia in caso di fallimento che di anomalie, azzerando l'overhead sul disco.

-------------------------------------------------------------------------------
5. PORTABILITÀ E SCALABILITÀ DEL SISTEMA
-------------------------------------------------------------------------------
L'architettura del software è stata sviluppata seguendo i criteri di massima 
indipendenza dall'ambiente operativo (Portabilità Cross-Platform):

* Astrazione dei Percorsi (OS-Agnostic): L'uso sistematico del modulo 'os.path' 
  garantisce la formattazione dinamica dei separatori di percorso (slash e backslash). 
  Il codice è nativamente pronto per girare indifferentemente su macchine Windows, 
  ambienti Linux nativi o server di calcolo remoto.
* Architettura Stateless dei Parametri: Le configurazioni, i seed numerici fino a 
  10^9 e gli ID temporanei vengono generati e passati in modo isolato a ogni iterazione. 
  Questo approccio rende la pipeline intrinsecamente predisposta per una futura 
  transizione verso il Multiprocessing parallelo multi-core.
* Separazione dei Ruoli (Separation of Concerns): La separazione netta tra UI 
  (main.py), incapsulamento protetto (generators_manager.py), fabbriche di dominio 
  (generators.py), motori di calcolo esterni (solver.py, validator.py) e utility di 
  sistema (util.py) garantisce la massima manutenibilità. L'infrastruttura è già 
  strutturalmente pronta per supportare la futura espansione verso i vincoli 
  normativi complessi delle specifiche PPLTL (Ordering, Obligation).
===============================================================================