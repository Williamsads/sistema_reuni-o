# Inicializa o repositório Git local
git init

# Adiciona todos os arquivos do sistema
git add .

# Cria o commit inicial
git commit -m "Deploy Sistema de Reunião SARA"

Write-Host "`n--- PRÓXIMO PASSO MANUAL ---" -ForegroundColor Cyan
Write-Host "1. Vá em https://github.com/new e crie um repositório chamado 'sistema-reuniao'"
Write-Host "2. Copie os 3 comandos que o GitHub vai te mostrar sob '...or push an existing repository from the command line'"
Write-Host "   Eles se parecem com isso:"
Write-Host "   git remote add origin https://github.com/SEU_USUARIO/sistema-reuniao.git"
Write-Host "   git branch -M main"
Write-Host "   git push -u origin main"
Write-Host "`nExecute esses 3 comandos aqui neste terminal." -ForegroundColor Yellow
