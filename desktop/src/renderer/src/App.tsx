import { ElectricBorder } from './components/ElectricBorder/ElectricBorder'

import styles from './App.module.css'

export default function App(): React.JSX.Element {
  return (
    <div className={styles.shell}>
      <div className={styles.cardSlot}>
        <ElectricBorder>
          <div />
        </ElectricBorder>
      </div>
    </div>
  )
}
