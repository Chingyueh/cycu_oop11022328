lyrics = '''Hello darkness, my old friend
I've come to talk with you again
Because a vision softly creeping
Left its seeds while I was sleeping
And the vision that was planted in my brain
Still remains
Within the sound of silence
In restless dreams, I walked alone
Narrow streets of cobblestone
'Neath the halo of a street lamp
I turned my collar to the cold and damp
When my eyes were stabbed by the flash of a neon light
That split the night
And touched the sound of silence
And in the naked light, I saw
Ten thousand people, maybe more
People talking without speaking
People hearing without listening
People writing songs that voices never shared
And no one dared
Disturb the sound of silence
"Fools" said I, "You do not know
Silence like a cancer grows
Hear my words that I might teach you
Take my arms that I might reach you"
But my words, like silent raindrops fell
And echoed in the wells of silence
And the people bowed and prayed
To the neon god they made
And the sign flashed out its warning
In the words that it was forming
Then the sign said, "The words on the prophets are written on the subway walls
In tenement halls"
And whispered in the sound of silence'''

def count_silence(lyrics, word='silence'):
    count = 0
    words = lyrics. lower ().split() 
    for word in words:
        if word == 'silence':
            count += 1
    return count

print(count_silence(lyrics))
'''
When you're weary
Feeling small
When tears are in your eyes
I will dry them all
I'm on your side
Oh, when times get rough
And friends just can't be found
Like a bridge over troubled water
I will lay me down
Like a bridge over troubled water
I will lay me down
When you're down and out
When you're on the street
When evening falls so hard
I will comfort you
I'll take your part
Oh, when darkness comes
And pain is all around
Like a bridge over troubled water
I will lay me down
Like a bridge over troubled water
I will lay me down
Sail on, silver girl
Sail on by
Your time has come to shine
All your dreams are on their way
See how they shine
Oh, if you need a friend
I'm sailing right behind
Like a bridge over troubled water
I will ease your mind
Like a bridge over troubled water
I will ease your mind
'''
def count_silence(lyrics, word='bridge'):
    count = 0
    words = lyrics. lower ().split() 
    for word in words:
        if word == 'silence':
            count += 1
    return count

print(count_silence(lyrics))