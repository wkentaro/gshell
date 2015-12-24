# ZSH support
if [[ -n ${ZSH_VERSION-} ]]; then
    autoload -U +X bashcompinit && bashcompinit
fi

_gshell()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts=""

    if [[ ${opts} = "" ]] ; then
      opts="ls ll pwd cd rm download mkdir upload share"
    fi

    case "$prev" in
      cd|rm|download|share)
        opts=$(gshell ls)
        ;;
      upload)
        opts=$(command ls)
        ;;
    esac

    if [[ ${cur} = * ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" ${cur}) )
        return 0
    fi
}
complete -F _gshell gshell
