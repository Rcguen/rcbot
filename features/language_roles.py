from config import LANGUAGES

async def assign_language_role(member, lang):

    guild = member.guild

    role_name = f"{LANGUAGES[lang]} Speaker"

    role = discord.utils.get(guild.roles, name=role_name)

    if not role:

        role = await guild.create_role(name=role_name)

    await member.add_roles(role)