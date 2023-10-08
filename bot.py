import discord, os, glob, json, datetime
from discord import app_commands

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

directory = os.getcwd()
configfile = open(directory + '/config.json')
config = json.load(configfile)

embed_color = 0x2b2d31

if not os.path.exists(directory + '/accounts'): 
    os.mkdir(directory + '/accounts')
if not os.path.exists(directory + '/paccounts'): 
    os.mkdir(directory + '/paccounts')

async def sendLog(interaction, account, service, premium):
    channel = bot.get_channel(int(config["logs-channel-id"]))
    author_name = interaction.user.name + "#" + interaction.user.discriminator
    embed=discord.Embed()
    embed.set_author(name=author_name + ' - ' + str(interaction.user.id), icon_url=interaction.user.avatar.url)
    embed.description=f"{service}\n```{account}```"
    embed.set_footer(text="Generator Log")
    embed.timestamp = datetime.datetime.now()
    if premium:
        embed.color=0xebb733
    else:
        embed.color=0x2B2D31
    await channel.send(embed=embed)
    return

async def simpleEmbed(interaction, message, ephemeral):
    embed=discord.Embed()
    embed.description=f"{message}"
    embed.color=0x2B2D31
    await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

async def getFileName(file):
    file_name = file.split('\\', -1)[-1]
    return file_name.split('.', -1)[0]

async def getAccs(p):
    allAccounts = []
    if not p:
        for file in glob.glob(directory + '/accounts/*.txt'):
            with open(file, 'r', encoding='utf-8') as fp:
                x = len(fp.readlines())
            allAccounts.append(await getFileName(file) + ":" + str(x))
    else:
        for file in glob.glob(directory + '/paccounts/*.txt'):
            with open(file, 'r', encoding='utf-8') as fp:
                x = len(fp.readlines())
            allAccounts.append(await getFileName(file) + ":" + str(x))
    return allAccounts

async def accountDisplay(account_list):
    new_acc_list = []
    for i in account_list:
        rndmlist1 = i.split(":", 1)
        rndmlist1[1] = "`" + rndmlist1[1] + "`"
        new_acc_list.append(rndmlist1[0].upper() + " -> " + rndmlist1[1])
    return new_acc_list

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=config["guild-id"]))
    print("Bot: {0.user}".format(bot))

@bot.event
async def on_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CommandNotFound):
        print("Helo")
        await simpleEmbed(interaction, "Comando no encontrado.", True)

def normal_cooldown(interaction: discord.Interaction): 
    if not config['admin-cooldown'] and interaction.user.guild_permissions.administrator:
        return None
    else:
        return app_commands.Cooldown(1, config['cooldown-duration'])

@tree.command(name = "gen", description = "Generar una cuenta.", guild=discord.Object(id=config["guild-id"]))
@app_commands.checks.dynamic_cooldown(normal_cooldown)
async def gen(interaction: discord.Interaction, account: str):
    if (
        str(interaction.channel_id) != config["free-channel-id"]
        and config["channel-specific-switch"]
    ):
        print(f"ID del canal actual: {interaction.channel_id}")
        print(f"ID del canal configurado: {config['free-channel-id']}")
        await simpleEmbed(interaction, "Este no es el canal adecuado!", True)
        return
    channel = await interaction.user.create_dm()
    for file in glob.glob(directory + '/accounts/*.txt'):
        file_name = file.split('\\', -1)[-1]
        file_name = file_name.split('.', -1)[0]
        if file_name.lower() == account.lower():
            if os.stat(file).st_size == 0:
                await interaction.response.send_message("`" + file_name.upper() + "` esta agotado.")
                return
            with open(file, "r+", encoding = "utf-8") as fp:
                lines = len(fp.readlines())
                fp.seek(0, os.SEEK_END)
                pos = fp.tell() - 1
                while pos > 0 and fp.read(1) != "\n":
                    pos -= 1
                    fp.seek(pos, os.SEEK_SET)
                acc_line = fp.readline()
                if pos > 0:
                    fp.seek(pos, os.SEEK_SET)
                    fp.truncate()
            
            if lines <= 1:
                with open(file, "w", encoding = "utf-8") as f:
                    f.write('')
            genembed=discord.Embed(title="Cuenta Generada - " + file_name,
                        description="```" + acc_line +"```",
                        color=embed_color)
            genembed.set_footer(text=config["messages"]["embed-footer"])
            await channel.send(embed=genembed)
            await simpleEmbed(interaction, config["messages"]["account-generated"], False)
            if config["logs-switch"]:
                await sendLog(interaction, acc_line, file_name, False)
            return
    await simpleEmbed(interaction, config["messages"]["service-doesnt-exist"], True)

@gen.error
async def gencmd_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f'Este comando está en cooldown. Por favor, inténtalo de nuevo en {error.retry_after:.2f} seconds.', ephemeral=True)

def premium_cooldown(interaction: discord.Interaction):
    if not config['admin-cooldown'] and interaction.user.guild_permissions.administrator:
        return None
    elif not config['premium-cooldown']:
        return None
    else:
        return app_commands.Cooldown(1, config['premium-cooldown-duration'])

@tree.command(name="pgen", description="Generar una cuenta premium.", guild=discord.Object(id=config["guild-id"]))
async def pgen(interaction: discord.Interaction, account: str):
    if (
        str(interaction.channel_id) != config["premium-channel-id"]
        and config["channel-specific-switch"]
    ):
        await simpleEmbed(interaction, "Este no es el canal adecuado!", True)
        return
    
    user = interaction.user
    premium_role_id = config["premium-role-id"]

    # Verifica si el usuario tiene el rol premium
    if (
        premium_role_id is not None
        and int(premium_role_id) not in [role.id for role in user.roles]
    ):
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        return

    channel = await interaction.user.create_dm()
    for file in glob.glob(directory + '/paccounts/*.txt'):
        file_name = file.split('\\', -1)[-1]
        file_name = file_name.split('.', -1)[0]
        if file_name.lower() == account.lower():
            if os.stat(file).st_size == 0:
                await interaction.response.send_message("`" + file_name.upper() + "` esta agotado.")
                return
            with open(file, "r+", encoding = "utf-8") as fp:
                lines = len(fp.readlines())
                fp.seek(0, os.SEEK_END)
                pos = fp.tell() - 1
                while pos > 0 and fp.read(1) != "\n":
                    pos -= 1
                    fp.seek(pos, os.SEEK_SET)
                acc_line = fp.readline()
                if pos > 0:
                    fp.seek(pos, os.SEEK_SET)
                    fp.truncate()
            
            if lines <= 1:
                with open(file, "w", encoding = "utf-8") as f:
                    f.write('')
            genembed=discord.Embed(title="Cuenta Generada - " + file_name,
                        description="```" + acc_line +"```",
                        color=embed_color)
            genembed.set_footer(text=config["messages"]["embed-footer"])
            await channel.send(embed=genembed)
            await simpleEmbed(interaction, config["messages"]["account-generated"], False)
            if config["logs-switch"]:
                await sendLog(interaction, acc_line, file_name, False)
            return
    await simpleEmbed(interaction, config["messages"]["service-doesnt-exist"], True)


@pgen.error
async def gencmd_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message(config["messages"]["no-permissions"], ephemeral=True)
    elif isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f'Este comando está en cooldown. Por favor, inténtalo de nuevo en {error.retry_after:.2f} seconds.', ephemeral=True)

@tree.command(name = "create", description = "Crea un nuevo servicio. (ADMIN ONLY)", guild=discord.Object(id=config["guild-id"]))
@app_commands.checks.has_permissions(administrator=True)
async def create(interaction: discord.Interaction, premium: bool, name: str):
    if premium:
        if not os.path.exists(directory + '/paccounts'): 
            os.mkdir(directory + '/paccounts')
        open(directory + "/paccounts/" + name.lower() + ".txt", "x")
        await interaction.response.send_message("Nuevo servicio creado: ``" + name.lower() + "``")

    elif not premium:
        if not os.path.exists(directory + '/accounts'): 
            os.mkdir(directory + '/accounts')
        open(directory + "/accounts/" + name.lower() + ".txt", "x")
        await interaction.response.send_message("Nuevo servicio creado: ``" + name.lower() + "``")
    else:
        await interaction.response.send_message("Error?", ephemeral=True)

@tree.command(name="remove", description="Elimina un servicio. (ADMIN ONLY)", guild=discord.Object(id=config["guild-id"]))
@app_commands.checks.has_permissions(administrator=True)
async def remove(interaction: discord.Interaction, premium: bool, name: str):
    service_name = name.lower()

    if premium:
        if os.path.exists(directory + '/paccounts'):
            premium_log_file = directory + "/paccounts/" + service_name + ".txt"
            if os.path.exists(premium_log_file):
                os.remove(premium_log_file)
                await interaction.response.send_message(f'El servicio "{service_name}" ha sido eliminado.')
                return

    elif not premium:
        if os.path.exists(directory + '/accounts'):
            log_file = directory + "/accounts/" + service_name + ".txt"
            if os.path.exists(log_file):
                os.remove(log_file)
                await interaction.response.send_message(f'El servicio "{service_name}" ha sido eliminado.')
                return

    await interaction.response.send_message(f'No se encontró el servicio "{service_name}".')

@tree.command(name="restock", description="Restock cuentas para un servicio. (SOLO ADMINISTRADORES)", guild=discord.Object(id=config["guild-id"]))
@app_commands.checks.has_permissions(administrator=True)
async def restock(interaction: discord.Interaction, premium: bool, service: str, accounts: str):
    if premium:
        for file in glob.glob(directory + '/paccounts/*.txt'):
            if await getFileName(file) == service:
                account_list = accounts.split()
                with open(file, 'a') as fp:
                    for account in account_list:
                        if not fp.tell() == 0:
                            fp.write('\n')
                        fp.write(account)
                await interaction.response.send_message("Operación exitosa.", ephemeral=True)
                return
    elif not premium:
        for file in glob.glob(directory + '/accounts/*.txt'):
            if await getFileName(file) == service:
                account_list = accounts.split()
                with open(file, 'a') as fp:
                    for account in account_list:
                        if not fp.tell() == 0:
                            fp.write('\n')
                        fp.write(account)
                await interaction.response.send_message("Operación exitosa.", ephemeral=True)
                return
    else:
        await interaction.response.send_message("Error?", ephemeral=True)


@tree.command(name="setupchannelgen", description="Establecer canales para servicios premium y gratuitos.", guild=discord.Object(id=config["guild-id"]))
@app_commands.checks.has_permissions(administrator=True)
async def setup_channels(interaction: discord.Interaction, premium: bool, channel: discord.TextChannel):
    channel_id = str(channel.id)

    user = interaction.user
    guild = interaction.guild

    if premium:
        config["premium-channel-id"] = channel_id
        await interaction.response.send_message("Canal premium configurado correctamente.")
    else:
        config["free-channel-id"] = channel_id
        await interaction.response.send_message("Canal gratuito configurado exitosamente.")

    with open('config.json', 'w') as config_file:
        json.dump(config, config_file, indent=4)

@tree.command(name="setuppremiumrole", description="Establecer el rol premium.", guild=discord.Object(id=config["guild-id"]))
async def setup_role(interaction: discord.Interaction, premium_role: discord.Role):
    try:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("No tienes permisos de administrador para usar este comando.", ephemeral=True)
            return
        config["premium-role-id"] = str(premium_role.id)
        with open('config.json', 'w') as config_file:
            json.dump(config, config_file, indent=4)
        await interaction.response.send_message("El rol premium se estableció correctamente.")
    except Exception as e:
        print(f"Error al configurar el rol premium: {e}")
 
@tree.command(name="setupchannellog", description="Establecer el canal para logs.", guild=discord.Object(id=config["guild-id"]))
@app_commands.checks.has_permissions(administrator=True)
async def setup_logchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    channel_id = str(channel.id)

    config["logs-channel-id"] = channel_id
    await interaction.response.send_message("Canal de logs configurado exitosamente.")

    with open('config.json', 'w') as config_file:
        json.dump(config, config_file, indent=4)

@tree.command(name="setpremiumcooldown", description="Habilitar o deshabilitar el cooldown para rol premium.", guild=discord.Object(id=config["guild-id"]))
@app_commands.checks.has_permissions(administrator=True)
async def set_premiumcooldown(interaction: discord.Interaction, enable: bool):
    config["premium-cooldown"] = enable
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file, indent=4)
    
    if enable:
        await interaction.response.send_message("Premium cooldown ha sido habilitado.")
    else:
        await interaction.response.send_message("Premium cooldown ha sido deshabilitado.")

@tree.command(name="setadmincooldown", description="Habilitar o deshabilitar el cooldown para adminstrador.", guild=discord.Object(id=config["guild-id"]))
@app_commands.checks.has_permissions(administrator=True)
async def set_admincooldown(interaction: discord.Interaction, enable: bool):
    config["admin-cooldown"] = enable
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file, indent=4)
    
    if enable:
        await interaction.response.send_message("Admin cooldown ha sido habilitado.")
    else:
        await interaction.response.send_message("Admin cooldown ha sido deshabilitado.")

@tree.command(name="setlogsswitch", description="Habilitar o deshabilitar el uso de logs.", guild=discord.Object(id=config["guild-id"]))
@app_commands.checks.has_permissions(administrator=True)
async def set_logsswitch(interaction: discord.Interaction, enable: bool):
    config["logs-switch"] = enable
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file, indent=4)
    
    if enable:
        await interaction.response.send_message("Logs han sido habilitados.")
    else:
        await interaction.response.send_message("Logs han sido deshabilitados.")
        
@tree.command(name="setexclusivechannels", description="Habilitar o deshabilitar el uso de canales especificos para generar.", guild=discord.Object(id=config["guild-id"]))
@app_commands.checks.has_permissions(administrator=True)
async def set_specificchannels(interaction: discord.Interaction, enable: bool):
    config["channel-specific-switch"] = enable
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file, indent=4)
    
    if enable:
        await interaction.response.send_message("Canales especificos han sido habilitados.")
    else:
        await interaction.response.send_message("Canales especificos han sido deshabilitados.")
        
@setup_channels.error
async def setup_channels_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("No tienes permiso para usar este comando.", ephemeral=True)
    elif isinstance(error, app_commands.CommandInvokeError):
        await interaction.response.send_message("Se produjo un error al procesar el comando.", ephemeral=True)




@tree.command(name = "stock", description = "Mostrar el stock.", guild=discord.Object(id=config["guild-id"]))
async def stock(interaction: discord.Interaction):
    
    service_num = 0
    embed=discord.Embed(title="Stock",
                        description=config["messages"]["stock-description"],
                        color=embed_color)
    
    p = False
    account_list = await getAccs(p)
    new_acc_list = []

    if not len(account_list) <= 0:
        new_acc_list = await accountDisplay(account_list)
        embed.add_field(name="Generador Gratis", value='\n'.join(new_acc_list), inline=False)
        service_num = len(new_acc_list)
        del new_acc_list, account_list

    new_acc_list = []
    account_list = await getAccs(p = True)
    if not len(account_list) <= 0:
        new_acc_list = await accountDisplay(account_list)
        service_num = len(new_acc_list) + service_num
        embed.add_field(name="Generador Premium", value='\n'.join(new_acc_list), inline=False)

    if service_num <= 0:
        embed.description = config["messages"]["stock-empty-description"]

    embed.title = "Stock - " + str(service_num) +  " Servicios"
    
    embed.set_footer(text=config["messages"]["embed-footer"])
    await interaction.response.send_message(embed=embed)

bot.run(config['token'])
