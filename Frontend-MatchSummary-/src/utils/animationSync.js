/**
 * Utility pentru sincronizarea animatiilor CSS intre pagini
 * Stocheaza timestamp-ul cand animatia ar trebui sa inceapa
 */

const ANIMATION_DURATION = 20000 // 20 secunde in milisecunde
const STORAGE_KEY = 'animationStartTime'

/**
 * Obtine delay-ul animatiei pentru sincronizare
 * @returns {number} Delay-ul in secunde (poate fi negativ)
 */
export const getAnimationDelay = () => {
  const now = Date.now()
  let startTime = localStorage.getItem(STORAGE_KEY)
  
  if (!startTime) {
    // Prima data - seteaza timestamp-ul curent
    startTime = now.toString()
    localStorage.setItem(STORAGE_KEY, startTime)
  } else {
    startTime = parseInt(startTime, 10)
  }
  
  // Calculeaza cat timp a trecut de la start
  const elapsed = (now - startTime) % ANIMATION_DURATION
  
  // Returneaza delay-ul negativ pentru a face animatia sa inceapa de la punctul corect
  // Convertim din milisecunde in secunde si facem negativ
  return -(elapsed / 1000)
}

/**
 * Reseteaza timestamp-ul animatiei (optional, pentru debugging)
 */
export const resetAnimationSync = () => {
  localStorage.removeItem(STORAGE_KEY)
}

