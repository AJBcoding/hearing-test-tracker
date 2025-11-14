import { NavLink } from 'react-router-dom'
import { Group, Title } from '@mantine/core'
import classes from './Navigation.module.css'

export function Navigation() {
  return (
    <Group h="100%" px="md" justify="space-between">
      <Title order={3}>Hearing Test Tracker</Title>

      <Group gap="xl">
        <NavLink
          to="/dashboard"
          className={({ isActive }) => isActive ? classes.linkActive : classes.link}
        >
          Dashboard
        </NavLink>
        <NavLink
          to="/upload"
          className={({ isActive }) => isActive ? classes.linkActive : classes.link}
        >
          Upload Test
        </NavLink>
        <NavLink
          to="/tests"
          className={({ isActive }) => isActive ? classes.linkActive : classes.link}
        >
          All Tests
        </NavLink>
      </Group>
    </Group>
  )
}
