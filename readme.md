# ScopeFoundry for Schuck Lab

Please follow this guidelines 

## To make commits

1. Get write access.
2. Open Source Tree Software
3. Stage file(s) or just lines. It is good practice commit coherent junks of codes.
4. Press Commit. A good description is appreciated.

## Get Write access

Email to one of the administrators and follow the instructions send by Atlassian

**Administrators**

1. Benedikt Ursprung (benediktursprung at live.com)
2. Dr. Changwhan Lee 

## New microscope

1. Get Write Access

2. Get python through Anaconda and your conda console write:

   ```bash
   conda install numpy pyqt qtpy h5py pyqtgraph
   ```

3. Download Eclipse, get `PyDev` from `Help-> Eclipse Marketplace...` Environment and make sure you know your workspace folder.

4. Download source tree and add your account, (if you don't have one Get Write Access)

5. In Create a local folder called *scope_foundry* in your eclipse workspace folder.

6. clone `scope_foundry` repository from `schucklab` workspace to the local *scope_foundry* folder.

7. Think of a good *`name`* for your setup and make new branch called `name_microscope`

8. Make a new folder `name_microscope` and within that folder create. 
   1. an empty `__init__.py` file

   2. `app.py` which will be the main file 

   3. a folder called `measurements` which is a folder that will contain measurement scripts specific to that setup.

   4. In `.gitignore` file add the two lines:

      `name_microscope/log/`
      `name_microscope/data/`

      as you never want to sync files located there

9. Make an initial commit. When prompted you should map from `name_microscope`-remote branch to  `name_microscope`-local.

10. In Eclipse, 

    1. Open Perspective and choose PyDev
    2. Make a new Project called `scope_foundry`. Maybe you need to configure the Ananconda Interpreter

11. Happy development

12. Praise Ed Barnard.
