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

## New setup

1. Get Write Access

2. Download source tree and enter your credentials

3. Create a local folder called *scope_foundry*

4. clone `scope_foundry` repository from `schucklab` workspace to a local *scope_foundry* folder.

5. Think of a good *name* for your setup and make new branch: give it a setup `name_microscope`

6. Make a new folder at root level called `name_microscope` and within that folder create. 
   1. an empty `__init__.py` file
   
   2. `app.py` which will be the main file 
   
   3. a folder called `measurements` which is a folder that will contain measurement scripts specific to that setup.
   
   4. In `.gitignore` file add the two lines:
   
      `name_microscope/log/`
      `name_microscope/data/`
   
      as you never want to sync files located there
   
7. Make an initial commit. When prompted you should map from `name_microscope`-remote branch to  `name_microscope`-local.

8. Happy setup development

8. Praise Ed Barnard



