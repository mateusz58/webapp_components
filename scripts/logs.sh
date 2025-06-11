
show_help() {
    echo "📝 Shopify Analytics - Log Viewer"
    echo "================================"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -f, --follow     Follow log output (like tail -f)"
    echo "  -e, --errors     Show only error logs"
    echo "  -w, --web        Show only web service logs"
    echo "  -d, --db         Show only database logs"
    echo "  -n, --lines NUM  Number of lines to show (default: 100)"
    echo "  -h, --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -f            # Follow all logs"
    echo "  $0 -e -n 50      # Show last 50 error lines"
    echo "  $0 -w --follow   # Follow web service logs"
}

# Default values
FOLLOW=""
FILTER=""
SERVICE=""
LINES=100

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW="--follow"
            shift
            ;;
        -e|--errors)
            FILTER="grep -i error"
            shift
            ;;
        -w|--web)
            SERVICE="web"
            shift
            ;;
        -d|--db)
            SERVICE="db"
            shift
            ;;
        -n|--lines)
            LINES="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Build command
CMD="docker-compose logs --tail=$LINES $FOLLOW"

if [ -n "$SERVICE" ]; then
    CMD="$CMD $SERVICE"
fi

# Execute command
echo "📝 Showing logs (lines: $LINES, service: ${SERVICE:-all})..."
echo "============================================"

if [ -n "$FILTER" ]; then
    eval "$CMD" | eval "$FILTER"
else
    eval "$CMD"
fi