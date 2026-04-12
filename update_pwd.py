import paramiko
import sqlite3

# Get local password hash
conn = sqlite3.connect('C:/Users/20171/.oh-enterprise/data.db')
c = conn.cursor()
c.execute('SELECT password_hash FROM users WHERE username = ?', ('guorui',))
local_hash = c.fetchone()[0]
conn.close()

# Create SQL update file
sql = "UPDATE users SET password_hash = '" + local_hash + "' WHERE username = 'guorui';"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234')

sftp = ssh.open_sftp()
with sftp.file('/home/ai-app/update.sql', 'w') as f:
    f.write(sql)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('sqlite3 /home/ai-app/.oh-enterprise/data.db < /home/ai-app/update.sql && echo done')
print(stdout.read().decode('utf-8', errors='replace').strip())
err = stderr.read().decode('utf-8', errors='replace')
if err:
    print('Error:', err[:100])

ssh.close()
print('Password hash copied to server')