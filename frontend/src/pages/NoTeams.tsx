import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Coffee, Plus } from 'lucide-react'

export function NoTeams() {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <Coffee className="h-16 w-16 text-muted-foreground mb-6" />
      <h2 className="text-xl font-semibold mb-2">No teams yet</h2>
      <p className="text-muted-foreground text-center mb-8 max-w-sm">
        You're not a member of any team yet. Create a team to get started, or ask a colleague to send you an invite.
      </p>
      <Card className="w-full max-w-sm">
        <CardContent className="pt-6 space-y-4">
          <Link to="/teams/new">
            <Button className="w-full">
              <Plus className="h-4 w-4 mr-2" />
              Create a Team
            </Button>
          </Link>
          <p className="text-xs text-center text-muted-foreground">
            If you have an invite link, just click it and you'll be added automatically.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
