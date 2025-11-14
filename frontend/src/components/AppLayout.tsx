import { AppShell } from '@mantine/core'
import { Outlet } from 'react-router-dom'
import { Navigation } from './Navigation'

export function AppLayout() {
  return (
    <AppShell
      header={{ height: 60 }}
      padding="md"
    >
      <AppShell.Header>
        <Navigation />
      </AppShell.Header>

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  )
}
