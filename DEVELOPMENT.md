# Development

Subtrees:

    git remote add spectools git@bitbucket.org:chwalisz/spectools.git
    git subtree add --prefix wispy/spectools spectools master

    git remote add specmonapp git@bitbucket.org:chwalisz/specmonapp.git
    git subtree add --prefix telos/specmonapp specmonapp master

The command to update the sub-project at a later date becomes:

    git fetch spectools master
    git subtree pull --prefix wispy/spectools spectools master

    git fetch specmonapp master
    git subtree pull --prefix telos/specmonapp specmonapp master

Now we can use the subtree push command like the following:

    git subtree push --prefix wispy/spectools spectools master

    git subtree push --prefix telos/specmonapp specmonapp master
