#!/bin/bash

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Service configuration
SERVICE_NAME="telegram-channel-bot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
BOT_DIR=$(pwd)
LOG_FILE="${BOT_DIR}/install.log"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo -e "$1"
}

# Show banner
show_banner() {
    clear
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           🤖 Telegram Channel Bot Manager 🤖                ║"
    echo "║                                                              ║"
    echo "║              Advanced Bot Management System                  ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Show menu function
show_menu() {
    show_banner
    echo -e "${CYAN}Select an option:${NC}\n"
    echo -e "${GREEN}📦 Installation & Setup:${NC}"
    echo "  1) 🚀 Install Bot (Fresh Installation)"
    echo "  2) 🔄 Reinstall Bot (Clean & Reinstall)"
    echo "  3) 🗑️  Complete Uninstall"
    echo ""
    echo -e "${YELLOW}⚙️  Bot Management:${NC}"
    echo "  4) ▶️  Start Bot"
    echo "  5) ⏹️  Stop Bot"
    echo "  6) 🔄 Restart Bot"
    echo "  7) 📊 Show Bot Status"
    echo ""
    echo -e "${PURPLE}📋 Monitoring & Logs:${NC}"
    echo "  8) 📝 Show Live Logs"
    echo "  9) 📄 Show Recent Logs"
    echo "  10) 🧹 Clear Logs"
    echo ""
    echo -e "${BLUE}🔧 Advanced Options:${NC}"
    echo "  11) ⚙️  Update Configuration"
    echo "  12) 🔍 Test Bot Connection"
    echo "  13) 💾 Backup Database"
    echo "  14) 📈 Show Statistics"
    echo ""
    echo -e "${RED}15) 🚪 Exit${NC}"
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
}

# Check system requirements
check_requirements() {
    log "${YELLOW}Checking system requirements...${NC}"
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        log "${RED}❌ Please don't run this script as root!${NC}"
        exit 1
    fi
    
    # Check OS
    if [[ ! -f /etc/os-release ]]; then
        log "${RED}❌ Unsupported operating system!${NC}"
        exit 1
    fi
    
    # Check internet connection
    if ! ping -c 1 google.com &> /dev/null; then
        log "${RED}❌ No internet connection!${NC}"
        exit 1
    fi
    
    log "${GREEN}✅ System requirements check passed${NC}"
}

# Install system dependencies
install_dependencies() {
    log "${YELLOW}Installing system dependencies...${NC}"
    
    # Update package list
    sudo apt update
    
    # Install Python and required packages
    if ! command -v python3 &> /dev/null; then
        log "${YELLOW}Installing Python3...${NC}"
        sudo apt install -y python3 python3-pip python3-venv python3-dev
    fi
    
    # Install additional tools
    sudo apt install -y curl wget git sqlite3
    
    log "${GREEN}✅ System dependencies installed${NC}"
}

# Create virtual environment and install Python packages
setup_python_environment() {
    log "${YELLOW}Setting up Python environment...${NC}"
    
    # Remove existing virtual environment
    if [[ -d "venv" ]]; then
        rm -rf venv
    fi
    
    # Create new virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    else
        log "${RED}❌ requirements.txt not found!${NC}"
        exit 1
    fi
    
    log "${GREEN}✅ Python environment setup completed${NC}"
}

# Get configuration from user
get_configuration() {
    log "${YELLOW}Getting bot configuration...${NC}"
    
    echo -e "${CYAN}Please provide the following information:${NC}\n"
    
    # Bot Token
    while true; do
        read -p "🤖 Bot Token (from @BotFather): " BOT_TOKEN
        if [[ -n "$BOT_TOKEN" && ${#BOT_TOKEN} -gt 40 ]]; then
            break
        else
            echo -e "${RED}❌ Invalid bot token! Please try again.${NC}"
        fi
    done
    
    # Channel ID
    while true; do
        read -p "📢 Channel ID (with @, e.g., @mychannel): " CHANNEL_ID
        if [[ "$CHANNEL_ID" =~ ^@[a-zA-Z][a-zA-Z0-9_]{4,31}$ ]]; then
            break
        else
            echo -e "${RED}❌ Invalid channel ID! Please use format @channelname${NC}"
        fi
    done
    
    # Admin ID
    while true; do
        read -p "👤 Admin Telegram User ID (numeric): " ADMIN_ID
        if [[ "$ADMIN_ID" =~ ^[0-9]+$ && ${#ADMIN_ID} -ge 8 ]]; then
            break
        else
            echo -e "${RED}❌ Invalid admin ID! Please enter a numeric Telegram user ID.${NC}"
        fi
    done
    
    # Create .env file
    cat > .env << EOF
# Bot Configuration
BOT_TOKEN=${BOT_TOKEN}
CHANNEL_ID=${CHANNEL_ID}
ADMIN_ID=${ADMIN_ID}

# Database Configuration
DATABASE_PATH=bot.db

# Bot Settings
REFERRAL_REWARD=10
MIN_REFERRALS_FOR_CONTENT=5
BROADCAST_DELAY=1

# Generated on: $(date)
EOF
    
    log "${GREEN}✅ Configuration saved to .env file${NC}"
}

# Test bot connection
test_bot_connection() {
    log "${YELLOW}Testing bot connection...${NC}"
    
    if [[ ! -f ".env" ]]; then
        log "${RED}❌ Configuration file not found!${NC}"
        return 1
    fi
    
    source venv/bin/activate
    
    # Create test script
    cat > test_bot.py << 'EOF'
import asyncio
import sys
from aiogram import Bot
from config import BOT_TOKEN, ADMIN_ID

async def test_connection():
    try:
        bot = Bot(token=BOT_TOKEN)
        me = await bot.get_me()
        print(f"✅ Bot connected successfully!")
        print(f"Bot name: {me.first_name}")
        print(f"Bot username: @{me.username}")
        
        # Test sending message to admin
        await bot.send_message(ADMIN_ID, "🧪 Bot connection test successful!")
        print(f"✅ Test message sent to admin")
        
        await bot.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
EOF
    
    if python test_bot.py; then
        log "${GREEN}✅ Bot connection test passed${NC}"
        rm test_bot.py
        return 0
    else
        log "${RED}❌ Bot connection test failed${NC}"
        rm test_bot.py
        return 1
    fi
}

# Create systemd service
create_service() {
    log "${YELLOW}Creating systemd service...${NC}"
    
    sudo bash -c "cat > ${SERVICE_FILE}" << EOF
[Unit]
Description=Telegram Channel Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=${BOT_DIR}
Environment="PATH=${BOT_DIR}/venv/bin"
ExecStart=${BOT_DIR}/venv/bin/python ${BOT_DIR}/bot.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegram-bot

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=${BOT_DIR}

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable ${SERVICE_NAME}
    
    log "${GREEN}✅ Systemd service created and enabled${NC}"
}

# Main installation function
install_bot() {
    log "${BLUE}Starting bot installation...${NC}"
    
    check_requirements
    install_dependencies
    setup_python_environment
    get_configuration
    
    if test_bot_connection; then
        create_service
        
        echo -e "\n${GREEN}🎉 Installation completed successfully!${NC}\n"
        echo -e "${CYAN}Next steps:${NC}"
        echo -e "  • Use option 4 to start the bot"
        echo -e "  • Use option 7 to check bot status"
        echo -e "  • Use option 8 to view live logs"
        echo -e "\n${YELLOW}Bot files location: ${BOT_DIR}${NC}"
        echo -e "${YELLOW}Service name: ${SERVICE_NAME}${NC}"
        
        log "${GREEN}✅ Installation completed successfully${NC}"
    else
        log "${RED}❌ Installation failed due to connection test failure${NC}"
        echo -e "\n${RED}Installation failed! Please check your bot token and try again.${NC}"
    fi
}

# Uninstall function
uninstall_bot() {
    echo -e "${RED}⚠️  WARNING: This will completely remove the bot and all data!${NC}"
    echo -e "${YELLOW}The following will be deleted:${NC}"
    echo -e "  • Bot service and configuration"
    echo -e "  • Database and logs"
    echo -e "  • Python virtual environment"
    echo -e "  • All bot files (except source code)"
    echo ""
    read -p "Are you absolutely sure? Type 'DELETE' to confirm: " confirm
    
    if [[ "$confirm" == "DELETE" ]]; then
        log "${YELLOW}Starting complete uninstallation...${NC}"
        
        # Stop and remove service
        sudo systemctl stop ${SERVICE_NAME} 2>/dev/null
        sudo systemctl disable ${SERVICE_NAME} 2>/dev/null
        sudo rm -f ${SERVICE_FILE}
        sudo systemctl daemon-reload
        
        # Remove bot files
        rm -rf venv
        rm -f .env
        rm -f *.db
        rm -f *.log
        rm -f test_bot.py
        
        log "${GREEN}✅ Bot completely uninstalled${NC}"
        echo -e "\n${GREEN}✅ Uninstallation completed successfully!${NC}"
    else
        log "${YELLOW}Uninstallation cancelled by user${NC}"
        echo -e "${YELLOW}Uninstallation cancelled.${NC}"
    fi
}

# Reinstall function
reinstall_bot() {
    log "${YELLOW}Starting bot reinstallation...${NC}"
    echo -e "${YELLOW}This will remove the current installation and install fresh.${NC}"
    read -p "Continue? (y/N): " confirm
    
    if [[ $confirm == "y" || $confirm == "Y" ]]; then
        # Stop service
        sudo systemctl stop ${SERVICE_NAME} 2>/dev/null
        
        # Remove old installation (keep source code)
        rm -rf venv
        rm -f *.db
        rm -f *.log
        
        # Fresh installation
        install_bot
    else
        echo -e "${YELLOW}Reinstallation cancelled.${NC}"
    fi
}

# Service management functions
start_bot() {
    log "${YELLOW}Starting bot...${NC}"
    if sudo systemctl start ${SERVICE_NAME}; then
        log "${GREEN}✅ Bot started successfully${NC}"
        echo -e "${GREEN}✅ Bot started successfully!${NC}"
        sleep 2
        show_status
    else
        log "${RED}❌ Failed to start bot${NC}"
        echo -e "${RED}❌ Failed to start bot! Check logs for details.${NC}"
    fi
}

stop_bot() {
    log "${YELLOW}Stopping bot...${NC}"
    if sudo systemctl stop ${SERVICE_NAME}; then
        log "${GREEN}✅ Bot stopped successfully${NC}"
        echo -e "${GREEN}✅ Bot stopped successfully!${NC}"
    else
        log "${RED}❌ Failed to stop bot${NC}"
        echo -e "${RED}❌ Failed to stop bot!${NC}"
    fi
}

restart_bot() {
    log "${YELLOW}Restarting bot...${NC}"
    if sudo systemctl restart ${SERVICE_NAME}; then
        log "${GREEN}✅ Bot restarted successfully${NC}"
        echo -e "${GREEN}✅ Bot restarted successfully!${NC}"
        sleep 2
        show_status
    else
        log "${RED}❌ Failed to restart bot${NC}"
        echo -e "${RED}❌ Failed to restart bot! Check logs for details.${NC}"
    fi
}

# Status and monitoring functions
show_status() {
    echo -e "${BLUE}📊 Bot Status:${NC}\n"
    
    # Service status
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        echo -e "🟢 Service Status: ${GREEN}Active (Running)${NC}"
    else
        echo -e "🔴 Service Status: ${RED}Inactive (Stopped)${NC}"
    fi
    
    # Detailed systemd status
    echo -e "\n${CYAN}Detailed Status:${NC}"
    sudo systemctl status ${SERVICE_NAME} --no-pager -l
    
    # Show recent logs
    echo -e "\n${CYAN}Recent Logs (last 10 lines):${NC}"
    sudo journalctl -u ${SERVICE_NAME} -n 10 --no-pager
}

show_live_logs() {
    echo -e "${BLUE}📝 Live Logs (Press Ctrl+C to exit):${NC}\n"
    sudo journalctl -u ${SERVICE_NAME} -f
}

show_recent_logs() {
    echo -e "${BLUE}📄 Recent Logs (last 50 lines):${NC}\n"
    sudo journalctl -u ${SERVICE_NAME} -n 50 --no-pager
}


clear_logs() {
    read -p "Clear all bot logs? (y/N): " confirm
    
    if [[ $confirm == "y" || $confirm == "Y" ]]; then
        log "${YELLOW}Clearing logs...${NC}"
        
        # Clear systemd logs
        sudo journalctl --vacuum-time=1s -u ${SERVICE_NAME}
        
        # Clear local log files
        rm -f *.log
        
        log "${GREEN}✅ Logs cleared successfully${NC}"
        echo -e "${GREEN}✅ All logs cleared successfully!${NC}"
    else
        echo -e "${YELLOW}Log clearing cancelled.${NC}"
    fi
}

# Configuration management
update_configuration() {
    echo -e "${YELLOW}🔧 Update Bot Configuration${NC}\n"
    
    if [[ ! -f ".env" ]]; then
        echo -e "${RED}❌ Configuration file not found!${NC}"
        return 1
    fi
    
    echo -e "${CYAN}Current configuration:${NC}"
    grep -E "^(BOT_TOKEN|CHANNEL_ID|ADMIN_ID)" .env | sed 's/BOT_TOKEN=.*/BOT_TOKEN=***HIDDEN***/'
    echo ""
    
    echo -e "${CYAN}What would you like to update?${NC}"
    echo "1) Bot Token"
    echo "2) Channel ID"
    echo "3) Admin ID"
    echo "4) All settings"
    echo "5) Cancel"
    
    read -p "Select option (1-5): " choice
    
    case $choice in
        1)
            read -p "New Bot Token: " new_token
            sed -i "s/BOT_TOKEN=.*/BOT_TOKEN=${new_token}/" .env
            ;;
        2)
            read -p "New Channel ID: " new_channel
            sed -i "s/CHANNEL_ID=.*/CHANNEL_ID=${new_channel}/" .env
            ;;
        3)
            read -p "New Admin ID: " new_admin
            sed -i "s/ADMIN_ID=.*/ADMIN_ID=${new_admin}/" .env
            ;;
        4)
            get_configuration
            ;;
        5)
            echo -e "${YELLOW}Configuration update cancelled.${NC}"
            return 0
            ;;
        *)
            echo -e "${RED}❌ Invalid option!${NC}"
            return 1
            ;;
    esac
    
    echo -e "${GREEN}✅ Configuration updated!${NC}"
    echo -e "${YELLOW}💡 Restart the bot to apply changes.${NC}"
}

# Database backup
backup_database() {
    log "${YELLOW}Creating database backup...${NC}"
    
    if [[ ! -f "bot.db" ]]; then
        echo -e "${RED}❌ Database file not found!${NC}"
        return 1
    fi
    
    backup_name="bot_backup_$(date +%Y%m%d_%H%M%S).db"
    cp bot.db "backups/${backup_name}" 2>/dev/null || {
        mkdir -p backups
        cp bot.db "backups/${backup_name}"
    }
    
    echo -e "${GREEN}✅ Database backed up to: backups/${backup_name}${NC}"
    log "${GREEN}Database backed up to: backups/${backup_name}${NC}"
}

# Show statistics
show_statistics() {
    echo -e "${BLUE}📈 Bot Statistics${NC}\n"
    
    if [[ ! -f "bot.db" ]]; then
        echo -e "${RED}❌ Database not found!${NC}"
        return 1
    fi
    
    echo -e "${CYAN}Database Statistics:${NC}"
    
    # Users count
    users_count=$(sqlite3 bot.db "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
    echo -e "👥 Total Users: ${GREEN}${users_count}${NC}"
    
    # Active members
    members_count=$(sqlite3 bot.db "SELECT COUNT(*) FROM users WHERE is_member = 1;" 2>/dev/null || echo "0")
    echo -e "✅ Active Members: ${GREEN}${members_count}${NC}"
    
    # Total referrals
    referrals_count=$(sqlite3 bot.db "SELECT COUNT(*) FROM referrals;" 2>/dev/null || echo "0")
    echo -e "🔗 Total Referrals: ${GREEN}${referrals_count}${NC}"
    
    # Database size
    if [[ -f "bot.db" ]]; then
        db_size=$(du -h bot.db | cut -f1)
        echo -e "💾 Database Size: ${GREEN}${db_size}${NC}"
    fi
    
    # Log file size
    if [[ -f "bot.log" ]]; then
        log_size=$(du -h bot.log | cut -f1)
        echo -e "📝 Log File Size: ${GREEN}${log_size}${NC}"
    fi
    
    echo -e "\n${CYAN}System Information:${NC}"
    echo -e "🖥️  OS: $(lsb_release -d | cut -f2)"
    echo -e "🐍 Python: $(python3 --version | cut -d' ' -f2)"
    echo -e "💿 Disk Usage: $(df -h . | tail -1 | awk '{print $5}') used"
    echo -e "🧠 Memory Usage: $(free -h | grep '^Mem:' | awk '{print $3"/"$2}')"
}

# Error handling
handle_error() {
    local exit_code=$?
    local line_number=$1
    
    log "${RED}❌ Error occurred at line ${line_number} with exit code ${exit_code}${NC}"
    echo -e "${RED}❌ An error occurred! Check ${LOG_FILE} for details.${NC}"
    
    exit $exit_code
}

# Set error trap
trap 'handle_error $LINENO' ERR

# Main execution loop
main() {
    # Create log file
    touch "$LOG_FILE"
    log "${BLUE}Script started at $(date)${NC}"
    
    while true; do
        show_menu
        read -p "Enter your choice (1-15): " choice
        
        case $choice in
            1)
                install_bot
                ;;
            2)
                reinstall_bot
                ;;
            3)
                uninstall_bot
                ;;
            4)
                start_bot
                ;;
            5)
                stop_bot
                ;;
            6)
                restart_bot
                ;;
            7)
                show_status
                ;;
            8)
                show_live_logs
                ;;
            9)
                show_recent_logs
                ;;
            10)
                clear_logs
                ;;
            11)
                update_configuration
                ;;
            12)
                test_bot_connection
                ;;
            13)
                backup_database
                ;;
            14)
                show_statistics
                ;;
            15)
                log "${BLUE}Script ended at $(date)${NC}"
                echo -e "${GREEN}👋 Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Invalid option! Please select 1-15.${NC}"
                sleep 2
                ;;
        esac
        
        echo -e "\n${YELLOW}Press Enter to continue...${NC}"
        read
    done
}

# Run main function
main "$@"