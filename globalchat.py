global_channels = set()

async def send_global(client,message):

    for channel_id in global_channels:

        channel = client.get_channel(channel_id)

        if channel and channel.id != message.channel.id:

            await channel.send(
                f"🌍 {message.author.name}: {message.content}"
            )