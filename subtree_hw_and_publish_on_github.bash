#! /bin/bash
# subtrees a module, creates a github subtree and pushes.

# run this script:
# 	bash subtree_hw_and_publish_on_github.bash <module> 
# argument <module> is the target directory in ScopeFoundryHW 

# Requirements:
# Update GitRepoBaseURL
# install https://cli.github.com/

# tested with MINGW64 terminal
# 2023-01-27 Benedikt Ursprung

GitRepoBaseURL="https://github.com/UBene"


TargetModule="ScopeFoundryHW/$1"
NewRepo="HW_$1"
NewGitRepoName="HW_$1.git"
FoundryScopeRoot=$PWD

echo attempting to pull subtree from $TargetModule to ~/$NewGitRepoName

cd $HOME
echo "$PWD"
mkdir $NewGitRepoName
echo mkdir $NewGitRepoName
cd $NewGitRepoName
git init --bare

cd $FoundryScopeRoot
git subtree push --prefix $TargetModule ~/$NewGitRepoName main 

cd $HOME
git clone $NewGitRepoName
cd $HOME/$NewRepo
git checkout main

echo create public repo on github
gh repo create $NewRepo --public

echo attempting to push to $GitRepoBaseURL/$NewGitRepoName, 
git remote add github $GitRepoBaseURL/$NewGitRepoName
git push -u github main