import { ElectricBorder } from './components/ElectricBorder/ElectricBorder'

import styles from './App.module.css'

export default function App(): React.JSX.Element {
  return (
    <div className={styles.shell}>
      <ElectricBorder
        color="#c9a96e"
        speed={1}
        chaos={0.5}
        borderRadius={18}
        className={styles.borderHost}
      >
        <div className={styles.content} />
      </ElectricBorder>
    </div>
  )
}
