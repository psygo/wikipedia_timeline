import { createRoot } from 'react-dom/client';
import '../src/theme.css';
import portrait from '../../prototype/images/huang-longshi.png';
import {
  TimelineRail, TimelineItem, TimelineSection, TimelineColumn, TimelineGap,
  OutlineList, OutlineTable, ViewSwitcher, View,
} from '../src';

// The data, written once: every view reads the same elements.
const items = (
  <>
    <TimelineSection title="Early">
      <TimelineItem date="1612" title="The Go academy">The Tokugawa shogunate patronises the game.</TimelineItem>
      <TimelineItem date="March 2016" title="AlphaGo defeats Lee Sedol" image={portrait} imageWidth={120} caption="A picture">AlphaGo wins four games to one in Seoul.</TimelineItem>
    </TimelineSection>
    <TimelineSection title="Later">
      <TimelineItem date="2017" events={[{ title: 'AlphaGo Master', text: 'Wins 60 online games.' }, { title: 'Summit', text: 'Beats Ke Jie.' }]} summary="Two events" />
      <TimelineItem date="2020" title="With a sub timeline" sub={<TimelineItem date="Spring" title="First">Sub item one.</TimelineItem>}>Parent text.</TimelineItem>
    </TimelineSection>
  </>
);

function App() {
  return (
    <main style={{ maxWidth: '56em', margin: '0 auto', padding: '1em' }}>
      <h1>TimelineRail for React</h1>

      <h2>One set of data, several views</h2>
      <p>The timeline, the list, the table and the switcher are separate components. The switcher only shows one of its views.</p>
      <ViewSwitcher>
        <View label="Timeline" default><TimelineRail>{items}</TimelineRail></View>
        <View label="List"><OutlineList>{items}</OutlineList></View>
        <View label="Table"><OutlineTable>{items}</OutlineTable></View>
      </ViewSwitcher>

      <h2>Items</h2>
      <TimelineRail>
        <TimelineItem date="1612" title="The Go academy">
          The Tokugawa shogunate patronises the game and forms the houses of professional players.
        </TimelineItem>
        <TimelineItem date="1846" title="The Ear-Reddening Game">
          Shusaku's move 127 stuns Gennan Inseki; see <a href="https://en.wikipedia.org/wiki/Honinb%C5%8D_Shusaku">Honinbō Shūsaku</a>.
        </TimelineItem>
        <TimelineItem date="March 2016" title="AlphaGo defeats Lee Sedol" image={portrait} imageWidth={120} caption="A picture, with a caption">
          AlphaGo wins four games to one in Seoul.
        </TimelineItem>
        <TimelineItem date="2017" collapsible={false}>Not collapsible: no title and always open.</TimelineItem>
        <TimelineItem
          date="2020" title="With a sub timeline" collapsed
          sub={<><TimelineItem date="Spring" title="First">Sub item one.</TimelineItem><TimelineItem date="Autumn" title="Second">Sub item two.</TimelineItem></>}
        >
          Parent text.
        </TimelineItem>
        <TimelineItem date="2024" events={[{ title: 'Event A', text: 'First of two events on one dot.' }, { title: 'Event B', text: 'The second.' }]} summary="Two events" />
      </TimelineRail>

      <h2>Sections</h2>
      <TimelineRail>
        <TimelineSection title="Lower Paleolithic" id="lower" intro="Each section is collapsible; double-click a section dot to keep only it open.">
          <TimelineItem date="3.3 mya" title="Stone tools">Oldest known stone tools.</TimelineItem>
          <TimelineItem date="1.8 mya" title="Hand axe">Acheulean hand axes.</TimelineItem>
        </TimelineSection>
        <TimelineSection title="Middle Paleolithic" id="middle" collapsed>
          <TimelineItem date="400 kya" title="Fire">Controlled use of fire.</TimelineItem>
          <TimelineSection title="A section inside a section">
            <TimelineItem date="300 kya" title="Spears">Wooden spears.</TimelineItem>
          </TimelineSection>
        </TimelineSection>
        <TimelineSection title="Upper Paleolithic" collapsed>
          <TimelineItem date="40 kya" title="Cave art">Paintings.</TimelineItem>
        </TimelineSection>
      </TimelineRail>

      <h2>Side by side, grouped</h2>
      <TimelineRail grouped>
        <TimelineColumn title="Players">
          <TimelineItem date="1846" title="Shusaku">Plays move 127.</TimelineItem>
          <TimelineGap />
          <TimelineItem date="1998" title="Lee Sedol">Becomes a professional.</TimelineItem>
        </TimelineColumn>
        <TimelineColumn title="Programs">
          <TimelineGap />
          <TimelineItem date="2016" title="AlphaGo">Beats Lee Sedol.</TimelineItem>
          <TimelineItem date="2017" title="AlphaGo Zero">Learns from self-play.</TimelineItem>
        </TimelineColumn>
      </TimelineRail>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
