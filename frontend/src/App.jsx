import { Routes, Route } from 'react-router-dom'
import Predict from './pages/Predict'

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Predict />} />
      </Routes>
    </>
  )
}
