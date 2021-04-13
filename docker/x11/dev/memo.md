watch -n 30 -d 'docker stats --no-stream --all --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"'
