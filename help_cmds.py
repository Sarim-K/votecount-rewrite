import discord


class createHelpMessage:
	def __init__(self, title, description, colour, img=None):
		self.title = title
		self.description = description
		self.colour = colour
		self.img = img 


def help(usermessage, message, img=None):
	if usermessage == "$help setup":
		help_message = createHelpMessage("ADMIN ONLY: used to choose server's voting emotes; type 'NONE' if a specific emote isnt required", "$setup <:upvote:452121917462151169> <:rt:451882250884218881> <:downvote:451890347761467402>", 1)

	elif usermessage == "$help debug":
		help_message = createHelpMessage("ADMIN ONLY: enables printing to console", "$debug / $debug 0 / $debug 1", 1)

	elif usermessage == "$help blacklist_add":
		help_message = createHelpMessage("ADMIN ONLY: adds a user to the blacklist; their votes won't be counted", "$blacklist_add @user", 1)

	elif usermessage == "$help blacklist_remove":
		help_message = createHelpMessage("ADMIN ONLY: removes a user from the blacklist", "$blacklist_remove @user", 1)

	elif usermessage == "$help blacklist_view":
		help_message = createHelpMessage("ADMIN ONLY: view the blacklist", "$blacklist_view", 1)	

	elif usermessage == "$help karma":
		help_message = createHelpMessage("view a user's karma", "$karma or $karma @user", 1)	

	elif usermessage == "$help given":
		help_message = createHelpMessage("view how much karma a user's given", "$given or $given @user", 1)	

	elif usermessage == "$help customise":
		help_message = createHelpMessage("$customise [karma/given] [template name] [dark/light]", "templates: https://imgur.com/a/FpmGsQR", 1)

	else:  # catch-all help command
		help_message = createHelpMessage("commands:", "$setup\n$debug\n$blacklist_add\n$blacklist_remove\n$blacklist_view\n\n$karma\n$given\n$customise", 1)

	embed = discord.Embed(title=help_message.title, description=help_message.description, color=help_message.colour)
	embed.set_author(name=message.author, icon_url=message.author.avatar_url)

	if img is None:
		return embed
	else:
		return embed, img