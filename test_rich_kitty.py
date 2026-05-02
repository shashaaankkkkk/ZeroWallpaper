from rich.console import Console
from rich.segment import Segment

c = Console()
kitty_seq = "\033_Ga=q,t=d,i=31,f=24,s=1,v=1,C=1,c=1,r=1;AAAA\033\\"
# printing raw string might be sanitized
# c.print(kitty_seq) 

# Using Segment
c.print(Segment(kitty_seq, control=True))
