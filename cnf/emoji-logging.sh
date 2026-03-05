#!/usr/bin/env bash
# Emoji logging helpers for shell scripts and interactive bash.
# Install locations:
#   - /etc/emoji-logging.sh
#   - /etc/profile.d/emoji-logging.sh

emoji_log_return_or_exit() {
  return 0 2>/dev/null || exit 0
}

# Allow explicit opt-out.
if [[ "${EMOJI_LOG_DISABLE:-0}" = "1" ]]; then
  emoji_log_return_or_exit
fi

# If loaded from profile.d, propagate to non-interactive bash.
_EMOJI_LOG_SCRIPT="${BASH_SOURCE[0]:-${0:-emoji-logging.sh}}"
case "${_EMOJI_LOG_SCRIPT}" in
  */profile.d/emoji-logging.sh)
    _EMOJI_LOG_ROOT="${_EMOJI_LOG_SCRIPT%/profile.d/emoji-logging.sh}/emoji-logging.sh"
    if [[ -r "${_EMOJI_LOG_ROOT}" ]]; then
      _EMOJI_LOG_BASH_ENV="${_EMOJI_LOG_ROOT}"
    else
      _EMOJI_LOG_BASH_ENV="${_EMOJI_LOG_SCRIPT}"
    fi
    if [[ "${BASH_ENV:-}" != "${_EMOJI_LOG_BASH_ENV}" ]]; then
      export BASH_ENV="${_EMOJI_LOG_BASH_ENV}"
    fi
    unset _EMOJI_LOG_BASH_ENV _EMOJI_LOG_ROOT
    ;;
esac

# Guard against multiple sourcing.
if [[ -n "${_EMOJI_LOG_LIB:-}" ]]; then
  emoji_log_return_or_exit
fi
_EMOJI_LOG_LIB=1

detect_emoji_support() {
  [[ -t 2 ]] || return 1
  case "${LC_ALL:-}${LANG:-}${LC_CTYPE:-}" in
    *[Uu][Tt][Ff][-_]*8*) ;;
    *[Uu][Tt][Ff]8*) ;;
    *) return 1 ;;
  esac
  case "${TERM:-}" in
    dumb|linux) return 1 ;;
  esac
  return 0
}

set_emoji_vars() {
  if detect_emoji_support; then
    export EMOJI_OK=true
    export ICON_OK="✅"
    export ICON_BAD="🚫"
    export ICON_INFO="ℹ️"
    export ICON_WARN="⚠️"
    export ICON_SAD="😢"
    export ICON_DR="🧪"
    export ICON_REAL="🗃️"
    export ICON_FILE="📄"
    export ICON_BYTE="💾"
    export ICON_DUP="🔗"
    export ICON_SAVE="🪙"
    export ICON_LOADING="⏳"
    export ICON_CHECK="✔️"
    export ICON_CROSS="❌"
    export ICON_UPLOAD="⬆️"
    export ICON_DOWNLOAD="⬇️"
    export ICON_COPY="📋"
    export ICON_FOLDER="📂"
    export ICON_LINK="🔗"
    export ICON_NEW="🆕"
    export ICON_WARNING="⚠️"
    export ICON_TASK="📋"
    export ICON_SUCCESS="🏆"
  else
    export EMOJI_OK=false
    export ICON_OK="[OK]"
    export ICON_BAD="[NO]"
    export ICON_INFO="[INFO]"
    export ICON_WARN="[WARN]"
    export ICON_SAD=":("
    export ICON_DR="[DRY-RUN]"
    export ICON_REAL="[RUN]"
    export ICON_FILE="[F]"
    export ICON_BYTE="[B]"
    export ICON_DUP="[DUP]"
    export ICON_SAVE="[$]"
    export ICON_LOADING="[LOADING]"
    export ICON_CHECK="[CHECK]"
    export ICON_CROSS="[CROSS]"
    export ICON_UPLOAD="[UPLOAD]"
    export ICON_DOWNLOAD="[DOWNLOAD]"
    export ICON_COPY="[COPY]"
    export ICON_FOLDER="[FOLDER]"
    export ICON_LINK="[LINK]"
    export ICON_NEW="[NEW]"
    export ICON_WARNING="[WARNING]"
    export ICON_TASK="[TASK]"
    export ICON_SUCCESS="[SUCCESS]"
  fi
}

set_emoji_vars

: "${ICON_OK:=OK}"
: "${ICON_BAD:=ERR}"
: "${ICON_INFO:=INFO}"
: "${ICON_WARN:=WARN}"
: "${ICON_TASK:=TASK}"
: "${ICON_DR:=DRY}"
: "${ICON_REAL:=RUN}"
: "${ICON_LOADING:=...}"
: "${ICON_SUCCESS:=DONE}"

# 0=quiet 1=error 2=warn 3=info 4=debug
: "${LOG_LEVEL:=3}"
: "${LOG_PREFIX:=}"
: "${LOG_TS:=auto}"  # auto|on|off

log_isatty() {
  [[ -t 2 ]]
}

log_ts() {
  case "${LOG_TS}" in
    on) date +%H:%M:%S ;;
    auto) log_isatty && date +%H:%M:%S || echo -n "" ;;
    off|*) echo -n "" ;;
  esac
}

log_pfx() {
  local ts pfx out=""
  ts="$(log_ts)"
  pfx="${LOG_PREFIX:+${LOG_PREFIX} }"
  [[ -n "${ts}" ]] && out+="[${ts}] "
  out+="${pfx}"
  printf "%s" "${out}"
}

# $1=level_num $2=icon $3=label $4...=message
log_print() {
  local lvl="$1" ico="$2" lab="$3"
  shift 3
  (( LOG_LEVEL < lvl )) && return 0
  if [[ -n "${lab}" ]]; then
    printf "%s%s%s %s\n" "$(log_pfx)" "[${lab}] " "${ico}" "$*" >&2
  else
    printf "%s%s %s\n" "$(log_pfx)" "${ico}" "$*" >&2
  fi
}

log_debug()   { log_print 4 "${ICON_INFO}" "DBG" "$*"; }
log_info()    { log_print 3 "${ICON_INFO}" "" "$*"; }
log_warn()    { log_print 2 "${ICON_WARN}" "" "$*"; }
log_ok()      { log_print 3 "${ICON_OK}" "" "$*"; }
log_success() { log_print 3 "${ICON_SUCCESS}" "" "$*"; }
log_error()   { log_print 1 "${ICON_BAD}" "" "$*"; }
log_task()    { log_print 3 "${ICON_TASK}" "" "$*"; }
log_dry()     { log_print 3 "${ICON_DR}" "" "$*"; }
log_run()     { log_print 3 "${ICON_REAL}" "" "$*"; }
log_die()     { log_error "$*"; exit 1; }
