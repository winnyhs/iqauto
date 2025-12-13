Installer of start_medical.exe
* start_medical.exe : binary to install 
  - automatic runner for medical.exe
  
* start_medical_schd.xml : system scheduler option descriptor 
  - add start_medical.exe into scheduler
  - Run start_medical.exe whenever logging in the system

* start_medical.sed : 
  - MUST be saved with ANSI (Windows 1252) format [✔]
  - iexpress descriptor to make the install image
  - the way to create a new file and generate install.exe accordingly
    - Win + R --> iexpress.exe --> save sed under THE SAME folder
    - Human-generated version is not accepted by iexpress 
    - To identify; 
      - Install Progream = install.cmd
        (type it; do not browse the pull-downoption)  [✔]
      - Package name = install.exe
      - No restart
      - SED file = install.sed
  - MUST be: []
    - UseLongFileName=1
    - After updating the above, save with ANSI format (WESTERN Window 1252)
  
* install.cmd : install script in install.exe
  - MUST be saved in ANSI (Windows 1252) [✔]
  
* uninstall.cmd : uninstall script
  - MUST be saved in ANSI (Windows 1252) [✔]

* How to create install.exe again (with the existing install.sed) in : 
  iexpress /n install.sed

