if command -v mise >/dev/null 2>&1; then
	eval "$(mise activate zsh)"
elif [ -x "$HOME/.local/bin/mise" ]; then
	eval "$("$HOME/.local/bin/mise" activate zsh)"
fi

if (( ! $+functions[compdef] )); then
	autoload -Uz compinit
	compinit
fi
eval "$(zoxide init zsh)"
eval "$(try init "$HOME/Developer/tries")"

export CLICOLOR=1
export LSCOLORS=GxFxCxDxBxegedabagaced
PROMPT='%F{7}❬%m❭ %F{2}%1~%F{1} ●%f '
