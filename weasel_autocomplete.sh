#!/bin/bash
_weasel_autocomplete()
{
    local cur opts makefile_opts
    cur="${COMP_WORDS[COMP_CWORD]}"
    makefile_opts=$(cat Makefile | grep -Po '^\S+(?=:)' | xargs)
    opts="$makefile_opts --help -h"
    COMPREPLY=( $(compgen -W "$opts" -- "$cur" | xargs) )
    return 0
}
complete -F _weasel_autocomplete weasel
