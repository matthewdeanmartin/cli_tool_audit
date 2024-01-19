set -e
clear
cli_tool_audit --help
echo "---basic commands----"
cli_tool_audit interactive --help
echo "--------------------------"
cli_tool_audit freeze --help
echo "--------------------------"
cli_tool_audit audit --help
echo "--------------------------"
echo "---config edit----"
cli_tool_audit read --help
echo "--------------------------"
cli_tool_audit create --help
echo "--------------------------"
cli_tool_audit update --help
echo "--------------------------"
cli_tool_audit delete --help
echo "--------------------------"
#echo "---demo----"
#cli_tool_audit demo --help
